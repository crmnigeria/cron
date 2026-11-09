name: Set up cron-job.org jobs

# Manual only: nothing runs until you click "Run workflow" on the Actions tab.
on:
  workflow_dispatch:
    inputs:
      mode:
        description: "preview = change nothing, apply = make the changes, trial-off = delete all three trial jobs"
        type: choice
        options:
          - preview
          - apply
          - trial-off
        default: preview
      city_push:
        description: "Also create the send_city_push.php job (every 10 minutes)"
        type: boolean
        default: false

jobs:
  cronjobs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Run setup_cronjobs.py
        env:
          CRONJOB_API_KEY: ${{ secrets.CRONJOB_API_KEY }}
          CRON_SECRET_KEY: ${{ secrets.CRON_SECRET_KEY }}
          MODE: ${{ inputs.mode }}
          CITY_PUSH: ${{ inputs.city_push }}
        run: |
          ARGS=""
          if [ "$MODE" = "apply" ]; then ARGS="--apply"; fi
          if [ "$MODE" = "trial-off" ]; then ARGS="--apply --trial-off"; fi
          if [ "$CITY_PUSH" = "true" ]; then ARGS="$ARGS --city-push"; fi
          python scripts/setup_cronjobs.py $ARGS
