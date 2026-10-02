# Third-party dependency policy

Do not copy or clone floating branches into this directory.

Each dependency must be reviewed and recorded with:

- upstream URL and immutable commit/tag;
- license and local modifications;
- ROS distribution and message compatibility;
- owner, update method and rollback procedure;
- a bag-replay or hardware smoke test.

Pinned evaluation dependencies are listed in the root `dependencies.repos`:

1. Livox-SDK2 `v1.3.1` commit for local, non-system installation;
2. `livox_ros_driver2` `1.2.6`, which includes MID360S support;
3. `Ericsii/FAST_LIO_ROS2` at an immutable commit, with an AgriSense-360
   frame-name patch applied after import.

FAST-LIO2 is GPL-2.0 and remains a separate third-party ROS process. Its pinned
commit is an evaluation candidate, not yet the production approval decision.

The project-owned packages must not be edited to hide untracked changes inside
vendored source. Changes to upstream code require a patch file or a documented fork.
