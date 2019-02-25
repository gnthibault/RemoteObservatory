import socket,logging,sys,json,time

class GuiderPHP2():

    def __init__(self,host,port):
        self.logger = logging.getLogger('clientPHD2')        
        self.logger.info('creating an instance of GuiderPHP2')

        self.host=str(host)
        self.port=port
        self.id=1
        self.recvBuf=""
        self.appState=""

    def connect(self):
        self.logger.info("<<<<<<< connect to server PHD2 server=%s  port=%d"%(self.host,self.port))

        # Create a socket (SOCK_STREAM means a TCP socket)
        self.sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.sock.setblocking(0)
        self.sock.settimeout(1.0)

        try:
            # Connect to server and send data
            self.sock.connect((self.host, self.port))
        except:
            self.logger.error("connection failed server PHD2 server=%s  port=%d"%(self.host,self.port))
            print sys.exc_info()[0]
            return "error"

        received = self.sock.recv(1024)
        return received

    def sendJson(self,jsonTxt):
        self.logger.info("send msg %s"%(jsonTxt[:-2]))
        try:
            self.sock.sendall(jsonTxt)
        except:
            self.logger.error("sendJSON failed")
            return ""
        self.getResponse()

    def closeServer(self):
        self.logger.info("<<<<<<< connection close with server PHD2")
        self.sock.close()

    def setConsigne(self,posX,posY):
        jsonTxt='{"jsonrpc":"2.0", "method": "set_lock_position", "params": {"x":%.1f , "y":%.1f }, "id":%d } \r\n'%(posX,posY,self.id)
        self.id+=1
        self.sendJson(jsonTxt)

    def setExposure(self,exposure):
        exposureMilli=int(exposure*1000)
        jsonTxt='{"jsonrpc":"2.0", "method": "set_exposure", "params": [%d], "id": %d} \r\n'%(exposureMilli,self.id)
        self.id+=1
        self.sendJson(jsonTxt)

    def loop(self):
        jsonTxt='{"jsonrpc":"2.0", "method": "loop", "params": [], "id":%d } \r\n'%(self.id)
        self.id+=1
        self.sendJson(jsonTxt)

    def stop(self):
        jsonTxt='{"jsonrpc":"2.0", "method": "stop_capture", "params": [], "id":%d } \r\n'%(self.id)
        self.id+=1
        self.sendJson(jsonTxt)

    def guide(self):
        jsonTxt='{"jsonrpc":"2.0", "method": "guide", "params": [{"pixels": 1.5, "time": 8, "timeout": 40}, false], "id":%d } \r\n'%(self.id)
        self.id+=1
        self.sendJson(jsonTxt)

    def receive(self):
        # Receive data from the server
        try:
            received = self.sock.recv(1024)
        except socket.timeout:
            self.logger.info("No response from server")
            return ""
        return received

    def getResponse(self):
        try:
            self.recvBuf += self.sock.recv(1024)
        except socket.timeout:
            pass
        
        msgs=self.recvBuf.split('\r\n')
        if len(msgs)==1:
            #msg not complete
            pass
        else:
            for msg in msgs[:-1]:
                try:
                    self.logger.info("-> received msg "+str(msg))
                    data=json.loads(msg)
                except:
                    self.logger.info("invalid json in response from Guider")
                    continue
                ks=data.keys()
                if "Event" in ks:
                    event=data['Event']
                    #print("Event %s"%event)
                    if event=="AppState":
                        print data
                        self.appState=data['State']
                    if event=="SettleDone":
                        self.settleStatus=data["Status"]
                        if "Error" in ks:
                            self.settleError=data["Error"] 
                    if event=="StarSelected":
                        print "Star selected"
                        self.starSelectX=data["X"]
                        self.starSelectY=data["Y"]
                        print("X=",self.starSelectX," Y=",self.starSelectY)
                    if event=="StarLost":
                        print "StarLost"
                        pass

            self.recvBuf=msgs[-1]


# exemple utilisation

if __name__ == "__main__":

    #exemple of asyncronus socket: https://dzone.com/articles/understanding
    # see here PHD2 protocol:  https://github.com/OpenPHDGuiding/phd2/wiki/EventMonitoring

    #load configuration file
    jsonTxt=open('./configAcquire.json').read()
    config=json.loads(jsonTxt)
    print (config)
    print ("--------------")

    # setup log file
    logging.basicConfig(filename=config['PHD2']['logFile'],level=logging.DEBUG,format='%(asctime)s %(message)s')

    # instantiate Guider class, set server and port
    server=config['PHD2']['server']
    guiderPHD2=GuiderPHP2(server['host'],server['port'])

    #connect
    guiderPHD2.connect()

    #set consigne
    posX=float(config['PHD2']['posX'])
    posY=float(config['PHD2']['posY'])
    guiderPHD2.setConsigne(posX,posY)

    #set exposure time
    guiderPHD2.setExposure(1.0)

    guiderPHD2.getResponse()
    print("app state=%s"%guiderPHD2.appState)

    #start loop
    guiderPHD2.loop()

    #start guide
    guiderPHD2.guide()
    guiderPHD2.getResponse()

    # attente
    st=15
    print("wait %d sec"%st)
    for i in range(st):
        time.sleep(1)
        guiderPHD2.getResponse()

    #stop guiding
    guiderPHD2.stop()
    guiderPHD2.getResponse()

    #close connection
    guiderPHD2.closeServer()
