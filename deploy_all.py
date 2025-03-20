from configparser import ConfigParser
import json
import logging
from pathlib import Path
from nemo_library import NemoLibrary
import traceback

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Path to the "Projekte" folder
base_path = Path(__file__).parent.parent.parent / "Projekte"
print(base_path)

# search for "srcdata" folder
if not base_path.exists():
    logging.error(f"Folder {base_path} does not exist")
    exit()
srcdatafolders = [folder for folder in base_path.rglob("srcdata")]
if not srcdatafolders:
    logging.error(f"No srcdata folder found in {base_path}")
    exit()

customers = [
    "siba",
    "ledlenser",
    "wepuko",
]
status = {}

for customer in customers:

    try:
        logging.info("*" * 80)
        logging.info(f"Deploying {customer}...")
        logging.info("*" * 80)

        # get credentials from config.ini
        config = ConfigParser()
        config.read("config.ini")
        tenant = config.get(f"nemo_library_{customer}", "tenant", fallback=None)
        userid = config.get(f"nemo_library_{customer}", "userid", fallback=None)
        password = config.get(f"nemo_library_{customer}", "password", fallback=None)
        environment = config.get(
            f"nemo_library_{customer}", "environment", fallback=None
        )

        # identifiy srcdata folder
        srcdatafolder = [
            folder for folder in srcdatafolders if customer in folder.parts
        ]
        if not srcdatafolder:
            logging.error(f"No srcdata folder found for {customer}")
            continue
        srcdatafolder = srcdatafolder[0]
        logging.info(f"Found srcdata folder: {srcdatafolder}")

        # build list of projects (=list of .csv files in srcdata folder)
        projects = [
            project.stem for project in srcdatafolder.glob("*.csv") if project.is_file()
        ]

        # remove " (ADD1)" and " (ADD2)" from projects
        projects = [
            project.replace(" (ADD1)", "").replace(" (ADD2)", "")
            for project in projects
        ]

        # get multi projects
        multi_projects = {}
        for project in projects:
            if "_" in project:
                multi_projects[project] = project.split("_", 1)[1]

        # remove "_" extensions from projects
        projects = [project.split("_", 1)[0] for project in projects]

        # get mappings
        mappingfolder = srcdatafolder.parent / "mappings"
        if not mappingfolder:
            logging.error(f"No mappings folder found for {customer}")
            continue

        mappings = [
            mapping.stem[8:]
            for mapping in mappingfolder.glob("*.csv")
            if mapping.is_file()
        ]

        logging.info(f"Found {len(projects)} projects in {srcdatafolder}")
        logging.info(f"Found {len(mappings)} mappings in {mappingfolder}")

        nl = NemoLibrary(
            tenant=tenant,
            userid=userid,
            password=password,
            environment=environment,
            migman_projects=projects,
            migman_local_project_directory=srcdatafolder.parent,
            migman_multi_projects=multi_projects,
            migman_mapping_fields=mappings,
        )

        precheckstatus = nl.MigManPrecheckFiles()
        if all([value == "ok" for key, value in precheckstatus.items()]):
            nl.MigManDeleteProjects()
            nl.MigManCreateProjectTemplates()
            nl.MigManLoadData()
            nl.MigManCreateMapping()
            nl.MigManLoadMapping()
            nl.MigManApplyMapping()
            nl.MigManExportData()
            status[customer] = "ok"
        else:
            status[customer] = "precheck not successfull"

    except Exception as e:
        logging.error(f"An error occurred while deploying {customer}: {e}")
        logging.error(traceback.format_exc())
        status[customer] = traceback.format_exc()
        continue

logging.info(f"status of projects: {json.dumps(status,indent=4)}")
