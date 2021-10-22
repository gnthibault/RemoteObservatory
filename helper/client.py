import time
import asyncio
import logging

"""
    INDIClient runs two tasks that are infinite loops and run 
    in parallel with the asyncio.gather function. These
    tasks, read_from_indiserver and write_to_indiserver, are 
    explained in the class diagram below. 

        Overall INDI server/client scheme
        --------------------------------------------
       
              ___________________________________________________________       
              | INDIClient                                              |   
              | ----------                                              |
 ____________ |                                                         |
 |          | |             ________________________             _______________________
 |          |---->reader--->|read_from_indiserver()|------------>|xml_from_indiserver()|
 |indiserver| |             ------------------------             -----------------------
 |          | |                                                         |
 |          | |             _______________________              _______|_______________
 |          |<-----writer---|write_to_indiserver()|<--to_indiQ<--|xml_to_indiserver()  |
 ------------ |             -----------------------              -----------------------
              |                                                         |
              -----------------------------------------------------------

    To build an INDIClient application sublcass INDIClient and override
    the xml_from_indiserver to retrieve data from the indiserver and
    use the xml_to_indiserver method to send data to the indiserver. An
    example of this is in webclient.py in this package.  

    TODO:
        it would be nice to remove tornado dependencies in this module. 

"""

class INDIClient:
    """This class sends/recvs INDI data to/from the indiserver 
    tcp/ip socket. See the above diagram for help understanding
    its data flow.  """


    def __init__(self, host="localhost", port=7624, read_width=30000):
        self.running = False
        self.client_connecting = False
        self.reader = None
        self.writer = False
        self.to_indiQ = asyncio.Queue() # Not threadsafe, use janus or aioprocessing if you want to use it directly
        self.port = port
        self.host = host
        self.read_width = read_width
        self.lastblob = None

    async def connect(self, timeout):
        """Attempt to connect to the indiserver in a loop.
        """
        while 1:
            task = None
            try:
                logging.debug(f"Attempting to connect to indiserver "
                              f"{self.host}:{self.port}")
                task = asyncio.open_connection(self.host, self.port)
                self.reader, self.writer = await asyncio.wait_for(task, timeout=timeout)
                logging.debug(f"Connected to indiserver {self.host}:{self.port}")
                # Send first "Introductory message" in non blocking fashion
                await self.to_indiQ.put("<getProperties version='1.7'/>")
                # Now run main two asynchronous task: consume send queue, and receive
                self.running = True
                # self.task = asyncio.gather(
                #     self.write_to_indiserver(timeout=timeout),
                #     self.read_from_indiserver())
                # await self.task
                task_write = asyncio.create_task(self.write_to_indiserver(timeout=timeout))
                task_read = asyncio.create_task(self.read_from_indiserver(timeout=timeout))
                await asyncio.wait([task_read, task_write], return_when=asyncio.FIRST_COMPLETED)

                logging.debug("INDI client tasks finished. indiserver crash?")
                logging.debug("Attempting to connect again")
            except ConnectionRefusedError:
                self.running = False
                logging.debug("Can not connect to INDI server\n")
            except asyncio.TimeoutError:
                logging.debug("Lost connection to INDI server\n")
            finally:
                if task is not None:
                    task.cancel()
            await asyncio.sleep(2.0)

    async def xml_from_indiserver(self, data):
        raise NotImplemented("This method should be implemented by the subclass")

    async def read_from_indiserver(self, timeout):
        """Read data from self.reader and then call
        xml_from_indiserver with this data as an arg."""
        while self.running:
            try:
                if self.reader.at_eof():
                    raise Exception("INDI server closed")
                # Read data from indiserver with a timeout, so that we don't block loop
                data = await asyncio.wait_for(self.reader.read(self.read_width),
                                              timeout=timeout)
            except asyncio.TimeoutError:
                continue
            except Exception as err:
                self.running = False
                logging.warning(f"Could not read from INDI server {err}")
                raise
            else:
                # Makes the data available for the application, and wait for it to be consumed
                await self.xml_from_indiserver(data)
        logging.warning(f"Finishing read_from_indiserver task")

    async def write_to_indiserver(self, timeout):
        """Collect INDI data from the from the to_indiQ.
        and send it on its way to the indiserver. 
        """
        while self.running:
            try:
                # Read from queue with a timeout, so that we don't block loop
                #to_indi = await asyncio.wait_for(self.to_indiQ.get(), timeout=0.1) #This was preventing subsequent call ?
                to_indi = self.to_indiQ.get_nowait()
            # except asyncio.TimeoutError:
            #     continue
            except asyncio.queues.QueueEmpty:
                await asyncio.sleep(0)
                continue
            try:
                logging.debug(f"Writing this to indi {to_indi}")
                self.writer.write(to_indi.encode())
                await asyncio.wait_for(self.writer.drain(), timeout=timeout)
            except Exception as err:
                self.running = False
                logging.error(f"Could not write to INDI server {err}")
        self.writer.close()
        await self.writer.wait_closed()
        logging.debug("Finishing write_to_indiserver task")