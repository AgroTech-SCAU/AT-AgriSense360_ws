# Generated outputs

This directory is reserved for generated maps and evaluation results. Binary
outputs such as `.pcd`, `.ply`, images and logs are local artifacts and are not
committed to Git.

The offline FAST-LIO2 helper creates `output/offline_lio/` automatically:

```bash
./tools/run_offline_lio.sh /absolute/path/to/rosbag2-directory
```

Do not use files in this directory as source configuration. Reproducible
configuration belongs under `src/<package>/config/`.
