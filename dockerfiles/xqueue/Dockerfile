FROM ubuntu:focal
 
ARG app_dir
ARG config_dir

RUN apt update && \
  apt-get install -y software-properties-common && \
  apt-add-repository -y ppa:deadsnakes/ppa && apt-get update && \
  apt-get install git-core language-pack-en python3-pip libmysqlclient-dev ntp libssl-dev python3.8-dev python3.8-venv python3-wheel jq awscli -qy && \
  rm -rf /var/lib/apt/lists/*

ENV VIRTUAL_ENV=/venv
RUN python3.8 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

RUN useradd -m --shell /bin/false app
RUN mkdir -p /edx/app/log/ /edx/app/xqueue
RUN touch /edx/app/log/edx.log /edx/app/xqueue/xqueue_cfg.yml
RUN chown app:app /edx/app/log/edx.log /edx/app/xqueue/xqueue_cfg.yml

WORKDIR /edx/app/xqueue
COPY ${app_dir}/requirements /edx/app/xqueue/requirements
COPY ${app_dir}/requirements.txt /edx/app/xqueue/requirements.txt
RUN pip install -r requirements.txt

USER app

EXPOSE 8040

COPY ${app_dir} /edx/app/xqueue
COPY ./${config_dir}/entrypoint.sh ./

ENV XQUEUE_CFG=/edx/app/xqueue/xqueue_cfg.yml
ENTRYPOINT ["/edx/app/xqueue/entrypoint.sh"]
