# Extra removal repair (outside frozen protocol)

- Task: `removal_0088_0` (spoon)
- Instruction: Remove the spoon in the bottom left and fill the area with the surrounding table texture.
- Route: BAGEL-7B-MoT NF4, 30 timesteps, seed 2026
- Input: original source image; output saved separately as `extra_repair/edited.png` on the VM
- Frozen first-output and planned repair counts: unchanged; this run is excluded from them.
- Visual comparison: spoon absent in both the frozen first edit and extra repair; the two outputs look very similar, with no clear added improvement by eye. No independent human ratings were collected for this extra run.
