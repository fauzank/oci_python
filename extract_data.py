import oci
from oci_services import OCIService

def execute_extract():
   # config = oci.config.from_file( "/.oci/config", "DEFAULT")

	# tenancy = Tenancy(config)
	# announcement = Announcement(config)

	# tenancy.print()
	# announcement.print()

   oci_service = OCIService()
   oci_service.extract_data()

execute_extract()
