# local includes
from Mount.IndiMount import IndiMount 
from helper.IndiClient import IndiClient

# ultra simplistic code
c = IndiClient.IndiClient(config=dict(indi_host = "localhost",indi_port = 7624))
c.connect()
m = IndiMount(c,config=dict(mount_name='Telescope Simulator'))
m.get_pier_side()
