# 11: Runtime, Observability, and MLOps

## Purpose

Run CPU and GPU analysis repeatably, control cost, diagnose failures, and preserve the lineage required to compare model versions.

## Local runtime

The first vertical slice should run with:

- Existing FastAPI and PostgreSQL services
- MinIO for original and derived objects
- A durable local queue or database-backed work queue
- CPU media worker with FFmpeg/ffprobe
- GPU-capable Python/PyTorch inference container where available
- CPU event, pattern, narrative, and clip workers

Workers share contracts through object artifacts and database records, not a common writable filesystem.

## Production runtime

Intended AWS mapping:

| Concern | Service |
| --- | --- |
| Originals and artifacts | S3 |
| Playback | CloudFront |
| Job events and buffering | EventBridge and SQS |
| Workflow state | PostgreSQL/RDS plus orchestration service |
| CPU preprocessing | AWS Batch or ECS tasks |
| GPU inference | AWS Batch managed GPU compute |
| Container images | ECR |
| Logs, metrics, alarms | CloudWatch |
| Secrets | Secrets Manager or Parameter Store |

AWS Batch supports GPU resource declarations for containerized jobs and managed GPU-capable compute. Do not run non-GPU stages on GPU instances without a measured reason.

## Container contract

Every job image must:

- Be pinned by digest in a pipeline release.
- Run as a non-root user when supported.
- Read only declared input objects.
- Write only to its job artifact prefix.
- Emit structured logs to stdout/stderr.
- Handle termination and checkpoint between chunks.
- Have CPU, memory, GPU, disk, and time limits.
- Avoid outbound internet access during media processing and inference.

## Version lineage

A pipeline release pins:

```text
pipeline version
preprocessing version
quality-gate version
court/player/pose/ball model versions
event-fusion version
pattern-rule version
narrative/template version
clip-policy version
container digests and configuration hashes
```

Do not overwrite a released model artifact. Register new weights and metrics as a new version. A model registry may be introduced when the number of models or environments warrants it; SageMaker Model Registry supports model versions, metadata, lineage, approval states, and deployment workflows.

## Metrics

### Reliability

- Jobs by status and failure code
- Queue age and stage latency
- Retry and cancellation counts
- Artifact-write failures
- Stuck jobs by stage

### Cost and throughput

- Video minutes processed
- CPU and GPU seconds per video minute
- Peak memory and temporary disk
- Derived storage bytes
- Cost per completed match and per published insight

### Model quality in production

- Quality-gate pass rate
- Unknown and review-required rate by event type
- Human correction rate by model version
- Insight withdrawal or material-change rate after review
- Drift by device, resolution, court surface, lighting, and capture profile

Do not use aggregate accuracy alone; monitor slices likely to expose performance gaps.

## Alarms

Alert on growing queue age, sustained job failure, missing artifacts, GPU capacity timeout, unusually high cost, analysis jobs stuck without heartbeat, and sudden changes in review/correction rates.

## Deployment

Promote a pipeline release only after offline evaluation. Support shadow processing on selected consented matches before changing the default. Keep the previous release available for rollback; do not mix artifacts from two pipeline releases inside one job.

## Acceptance criteria

- A job’s result can be reproduced from recorded versions and input checksum.
- Operators can identify cost and failure stage for each match.
- Workers cannot access arbitrary user object prefixes.
- Rollback selects the prior complete pipeline release.
- A model change cannot reach production without its evaluation report.

## References

- [AWS Batch GPU jobs](https://docs.aws.amazon.com/batch/latest/userguide/gpu-jobs.html)
- [SageMaker Model Registry](https://docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html)

