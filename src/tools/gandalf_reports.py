#!/usr/bin/env python3
import sys
import json
import logging
import pandas as pd
import typer

app = typer.Typer()


def load_summaries(file):
    """
    Open deployment summaries JSON file, load into
    Pandas and return as a DF
    """
    logging.info('load_summaries(%s)', file)

    try:
        df = pd.read_json(file)
        return df
    except ValueError:
        logging.warning('load_summaries(%s): Failed to open file.', file)
        sys.exit()


def run_reports():
    """
    main entry point
    """
    logging.info('run_reports()')
    sf = '/data/gandalf/gandalf_configs/deployment_summaries/summaries.json'
    df = load_summaries(sf)
    gf = (df.groupby('operator'))
    sf = df.loc[df['deployed'].str.contains("2022", case=True)]
    sf = sf.groupby('operator')
    print(sf.agg({'days_wet': ['sum','count']}))

if __name__ == '__main__':
     logging.basicConfig(level=logging.INFO)
     logging.info('gandalf_reports')
     run_reports()
