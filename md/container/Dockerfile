# GROMACS molecular dynamics
# Runs Jupyter notebooks and CLI tools (gmx, etc.)
# start.sh honors JUPYTER_BASE_URL / JUPYTER_TOKEN for Ephemeral gateway.
FROM condaforge/mambaforge:latest

# Do not use /workspace/* here: gcsfuse bind-mounts /workspace and Docker would create
# an empty notebooks/ folder at the user's Files home root on every session start.
WORKDIR /opt/tomo

COPY environment.yml .
RUN mamba env create -f environment.yml && mamba clean -afy

ENV PATH="/opt/conda/envs/gromacs/bin:$PATH"

COPY jupyter_notebook_config.py start.sh /opt/tomo/
RUN chmod +x /opt/tomo/start.sh

EXPOSE 8888
CMD ["/opt/tomo/start.sh"]
