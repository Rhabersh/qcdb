from sqlalchemy import *
from sqlalchemy.orm import Session
from qcdb.connection import connection
import glob2
import oyaml as yaml
import os
import pandas as pd
import argparse
import logging
import sys
from qcdb.parsers.qckitfastq_parse import qckitfastqParser
from qcdb.parsers.fastqc_parse import fastqcParser

# Initialize the logger
log = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
handler.setLevel(logging.INFO)
log.addHandler(handler)
log.setLevel(logging.INFO)

parser = argparse.ArgumentParser()
parser.add_argument('--file', '-f', help='Location of params.yaml')

def insert(results, m, session):
    log.info("Loading metadata for {}...".format(results.sample_id))
    
    s = m.tables['samplemeta']
    # check if sample_id is in table already
    q = session.query(s).filter(s.c.sample_id==results.sample_id)
    if not session.query(q.exists()).scalar():
        session.execute(s.insert().values(sample_id=results.sample_id,
            sample_name=results.sample_name,
            library_read_type=results.library_read_type,
            experiment=results.experiment))
        session.commit()

    # insert results v into each table k
    for k,v in results.tables.items():
        log.info("Loading {} ...".format(k))
        t = m.tables[k]
        session.execute(t.insert(),v)
        session.commit()

# temporary solution to get file handles for
# qckitfastqParser and picardToolsParser
def split_helper(files):
    unique_files = set()
    for f in files:
        base_file = os.path.basename(f)
        dirname = os.path.dirname(f)
        spl = base_file.split('_')
        if spl[2][0].isalpha():
            s = spl[:2]
            s.append("se")
            unique_files.add(os.path.join(dirname,"_".join(s)))
        else:
            s = spl[:3]
            unique_files.add(os.path.join(dirname,"_".join(s)))
    return unique_files

# parse and load metadata
def parse(d, m, session):
    # parse and load metadata
    for module in d['files']['module']:
        directory = module['directory']

        try:
            if module['name'] == 'fastqc':
                files = glob2.glob(os.path.join(directory, '*_fastqc.zip'))
                if not files:
                    log.error("No fastqc output found in: {}".format(directory))
                for f in files:
                    results = fastqcParser(f)
                    insert(results, m, session)
            elif module['name'] == 'qckitfastq':
                files = split_helper(glob2.glob(os.path.join(directory, '*.csv')))
                if not files:
                    log.error("No qckitfastqc output found in: {}".format(directory))
                for f in files:
                    results = qckitfastqParser(f)
                    insert(results, m, session)
        except:
            log.error("Error in parsing...")

def main(config):
    # Load load.yaml file
    with open(config, 'r') as io:
        d = yaml.load(io)

    db = d['db']['name']
    params = d['db']['params']
    # start connection
    conn = connection(params=params, db=db)
    log.info("Connected to {0}:{1}:{2}".format(params['host'],
                                            params['port'],
                                            db))
    session = Session(bind=conn)
    m = MetaData()
    m.reflect(bind=conn)

    parse(d, m, session)

if __name__ == '__main__':
    args = parser.parse_args()
    config = str(args.file)
    main(config)
