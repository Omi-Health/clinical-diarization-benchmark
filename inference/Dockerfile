FROM nvcr.io/nvidia/pytorch@sha256:ace9a848c0ae543317e3c4763b6b4248961c47902625abfe3c77a0fb931c50fb
COPY inference/environment-constraints.txt /tmp/constraints.txt
RUN apt-get update -qq && apt-get install -y -qq libsndfile1 ffmpeg git && \
    python -m pip install -c /tmp/constraints.txt Cython packaging soundfile boto3 huggingface_hub && \
    python -m pip install -c /tmp/constraints.txt 'nemo_toolkit[asr] @ git+https://github.com/NVIDIA/NeMo.git@2d902060e8dc5f65e6e49cf67341745b4a7e42b2'
WORKDIR /work/repo
