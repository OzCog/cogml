"""
An example implementation of the interface defined in client.py

Important: An OpenCog server must be running in the background and the REST API
must be loaded before running this script.

Runs 'num_steps' cycles. At each discrete timestep, captures the STI values of
the atoms in the attentional focus, and also capture a Scheme dump of the
attentional focus. When finished, exports the STI timeseries dataset to
'output_filename'.

Read README.md before running this example.
"""

__author__ = 'Cosmo Harrigan'

from opencog import *

# Configurable parameters:
num_steps = 50                            # Number of time steps
output_filename = 'ecan-timeseries.csv'   # Output filename

# PLN agent parameters
agent_path = "../opencog/python/pln/examples/tuffy/smokes/smokes_agent"
agent_name = "InferenceAgent"

# Launch an OpenCog server as a background process
server = Server()
#server.start()

# Initialize the CogServer. This script can be ran multiple times without
# restarting the CogServer, since it will clear the contents of the atomspace
# each time.
clear_atomspace()
set_af_boundary(10)

# The agent loop needs to be stopped so that we can manually step agents, to
# allow for data to be captured between each step.
stop_agent_loop()

load_python_agent(agent_path)
start_python_agent(agent_path, agent_name)

load_scheme_files(["python/pln/examples/tuffy/smokes/smokes.scm",
                   "python/pln/examples/tuffy/smokes/extra-data.scm"])

# The PLN agent will constantly give stimulus to the query
scheme("(define query hasCancer)")

# Set the configuration parameters for diffusion
set_stimulus_amount("20")
set_diffusion_percent("0.50")
set_wages("3")
set_rent("8")

af_timeseries = []
atomspace_timeseries = []

for t in range(0, num_steps):
    af_point_in_time = get_attentional_focus(timestep=t, scheme=True)
    atomspace_point_in_time = get_atomspace(timestep=t, scheme=True)
    af_timeseries.append(af_point_in_time)
    atomspace_timeseries.append(atomspace_point_in_time)

    importance_diffusion()
    importance_updating()
    step_python_agent(agent_path, agent_name)

    print("Timestep {0}, {1} atoms captured in attentional focus. "
          "{2} atoms captured in atomspace."
          .format(t, len(af_point_in_time['atoms']),
                  len(atomspace_point_in_time['atoms'])))

    print "People with cancer: {0}".format(
        scheme("(count-people-with-cancer)"))

#export_timeseries_mongodb(af_timeseries)
export_timeseries_mongodb(atomspace_timeseries)
export_timeseries_csv(atomspace_timeseries, "output.csv", scheme=False)
