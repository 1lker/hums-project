# PRD-002 — Multi-language reproducible environment.
#
# Python 3.14 for the data pipeline. Stage 2 (commented, enabled in PRD-003)
# adds Blender + IfcOpenShell for BIM generation.

FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libproj-dev \
    libgeos-dev \
    libxml2-dev \
    libxslt-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip setuptools wheel && pip install -r requirements.txt

COPY src ./src
ENV PYTHONPATH=/work/src
CMD ["python", "-m", "hums", "prd001"]

# -- future stage (PRD-003) --------------------------------------------------
# FROM base AS bim
# RUN apt-get update && apt-get install -y blender && \
#     pip install ifcopenshell blenderbim
# CMD ["blender", "--background", "--python", "src/hums/render/blender_entry.py"]
