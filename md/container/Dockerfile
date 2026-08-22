# GROMACS molecular dynamics
# Runs Jupyter notebooks and CLI tools (gmx, etc.)
# start.sh honors JUPYTER_BASE_URL / JUPYTER_TOKEN for Ephemeral gateway.
FROM condaforge/mambaforge:latest

WORKDIR /workspace/notebooks

COPY environment.yml .
RUN mamba env create -f environment.yml && mamba clean -afy

ENV PATH="/opt/conda/envs/gromacs/bin:$PATH"

COPY jupyter_notebook_config.py start.sh /opt/tomo/
RUN chmod +x /opt/tomo/start.sh

EXPOSE 8888
CMD ["/opt/tomo/start.sh"]
