export PATH=/home/dbe/miniconda3/bin:$PATH

source /home/dbe/miniconda3/etc/profile.d/conda.sh

conda deactivate
conda activate vis

PORT={{ visualisation_port }}
PORT_BACKEND={{ incoming_data_port }}

H=`echo ${HOSTNAME} | sed 's/.psi.ch//'`
BACKEND=${H}

CORES="{{ visualisation_cores }}"

taskset -c ${CORES} \
streamvis {{ visualisation_view }} --allow-websocket-origin=${H}:${PORT} --allow-websocket-origin={{ alias_visualisation }}:${PORT} \
--port=${PORT} --address  tcp://${BACKEND}:${PORT_BACKEND} \
--page-title {{ visualisation_title }}

