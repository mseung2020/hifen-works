FROM python:3.11-slim

RUN useradd -m -u 1000 user
USER user
WORKDIR /home/user/app

ENV PATH="/home/user/.local/bin:$PATH"

COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

COPY --chown=user:user . .

ENV PORT=7860
EXPOSE 7860

CMD ["python", "quadrant_cluster_app.py"]
