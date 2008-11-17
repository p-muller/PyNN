"""
A collection of utility functions.
$Id:$
"""

# If there is a settings.py file in the PyNN root directory, defaults will be
# taken from there.
try:
    from pyNN.settings import SMTPHOST, EMAIL
except ImportError:
    SMTPHOST = None
    EMAIL = None
import sys
import logging

red     = 0010; green  = 0020; yellow = 0030; blue = 0040;
magenta = 0050; cyan   = 0060; bright = 0100
try:
    import ll.ansistyle
    def colour(col, text):
        return str(ll.ansistyle.Text(col,str(text)))
except ImportError:
    def colour(col, text):
            return text


def notify(msg="Simulation finished.", subject="Simulation finished.", smtphost=SMTPHOST, address=EMAIL):
        """Send an e-mail stating that the simulation has finished."""
        if not (smtphost and address):
            print "SMTP host and/or e-mail address not specified.\nUnable to send notification message."
        else:
            import smtplib, datetime
            msg = ("From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n") % (address,address,subject) + msg
            msg += "\nTimestamp: %s" % datetime.datetime.now().strftime("%H:%M:%S, %F")
            server = smtplib.SMTP(smtphost)
            server.sendmail(address, address, msg)
            server.quit()

def get_script_args(script, n_args):
    script_index = sys.argv.index(script)
    args = sys.argv[script_index+1:script_index+1+n_args]
    if len(args) != n_args:
        raise Exception("Script requires %d arguments, you supplied %d" % (n_args, len(args)))
    return args
    
def init_logging(logfile, debug=False, num_processes=1, rank=0):
    if num_processes > 1:
        logfile += '.%d' % rank
    if debug:
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=logfile,
                    filemode='w')
    else:
        logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=logfile,
                    filemode='w')
        
        
class MultiSim(object):
    """
    A small framework to make it easier to run the same model on multiple
    simulators.
    
    Currently runs the simulations interleaved, but it would be nice to add
    parallel runs via threading, multiple processes, or MPI processes.
    """
    
    def __init__(self, sim_list, net, parameters):
        """
        Build the model defined in the class `net`, with parameters `parameters`,
        for each of the simulator modules specified in `sim_list`.
        
        The `net` constructor takes arguments `sim` and `parameters`.
        """
        self.sim_list = sim_list
        self.nets = {}
        for sim in sim_list:
            self.nets[sim.__name__] = net(sim, parameters)
            
    def __iter__(self):
        return self.nets.itervalues()
    
    def __getattr__(self, name):
        """
        Assumes `name` is a method of the `net` model.
        Return a function that runs `net.name()` for all the simulators.
        """
        def iterate_over_nets(*args, **kwargs):
            retvals = {}
            for sim_name, net in self.nets.items():
                retvals[sim_name] = getattr(net, name)(*args, **kwargs)
            return retvals
        return iterate_over_nets
            
    def run(self, simtime, steps=1, *callbacks):
        """
        Run the model for a time `simtime` in all simulators.
        
        The run may be broken into a number of steps (each of equal duration).
        Any functions in `callbacks` will be called after each step.
        """
        dt = float(simtime)/steps
        for i in range(steps):
            for sim in self.sim_list:
                sim.run(dt)
            for func in callbacks:
                func()
                
    def end(self):
        for sim in self.sim_list:
            sim.end()
            