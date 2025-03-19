from configparser import ConfigParser
import logging
from pathlib import Path
from nemo_library import NemoLibrary

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
    "wepuko"
]

for customer in customers:
    
    logging.info(f"Deploying {customer}...")

    # get credentials from config.ini
    config = ConfigParser()
    config.read("config.ini")
    tenant = config.get(f"nemo_library_{customer}", "tenant", fallback=None)
    userid = config.get(f"nemo_library_{customer}", "userid", fallback=None)
    password = config.get(f"nemo_library_{customer}", "password", fallback=None)
    environment = config.get(f"nemo_library_{customer}", "environment", fallback=None)

    # identifiy srcdata folder
    srcdatafolder = [folder for folder in srcdatafolders if customer in folder.parts]
    if not srcdatafolder:
        logging.error(f"No srcdata folder found for {customer}")
        continue
    srcdatafolder = srcdatafolder[0]    
    logging.info(f"Found srcdata folder: {srcdatafolder}")  
    
    # build list of projects (=list of .csv files in srcdata folder) 
    projects = [project.stem for project in srcdatafolder.glob("*.csv") if project.is_file()]
    # remove " (ADD1)" and " (ADD2)" from projects
    projects = [project.replace(" (ADD1)","").replace(" (ADD2)","") for project in projects]
    logging.info(f"Found {len(projects)} projects in {srcdatafolder}")  
    
    nl = NemoLibrary(
        tenant=tenant,
        userid=userid,
        password=password,
        environment=environment,
        migman_projects=projects,
        migman_local_project_directory=srcdatafolder.parent,
    )
    
    nl.MigManDeleteProjects()
    nl.MigManCreateProjectTemplates()
    nl.MigManLoadData()