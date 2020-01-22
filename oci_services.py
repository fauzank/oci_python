import oci
import time
import requests

config = None
report_no = None
par_url = None

class OCIService(object):
   def __init__(self):
      global report_no
      global par_url

      self.config = oci.config.from_file( "/.oci/config", "DEFAULT")
      par_url = self.config[ 'par' ]
      timetup = time.gmtime()
      report_no = time.strftime('%Y-%m-%dT%H:%M:%SZ', timetup).replace( ':', '-')

   def extract_data(self):
      tenancy = Tenancy(self.config)
      announcement = Announcement(self.config)
      limit = Limit( self.config, tenancy )
      compute = Compute( self.config, tenancy)
      boot_volume = BootVolume(self.config, tenancy)
      block_volume = BlockVolume(self.config, tenancy)    
      db_system = DBSystem( self.config, tenancy )

      tenancy.print()
      announcement.print()
      limit.print()
      compute.print()
      boot_volume.print()
      block_volume.print()
      db_system.print()

class Tenancy(object):
   tenancy_id = None
   name = None
   description = None
   home_region = None

   compartments = []
   regions = None
   availability_domains = []
   limit_summary = []

   def __init__(self, config):
      self.tenancy_id = config["tenancy"]

      identity = oci.identity.IdentityClient(config)

      tenancy = identity.get_tenancy( self.tenancy_id ).data

      self.name = tenancy.name
      self.description = tenancy.description
      self.home_region = tenancy.home_region_key

      self.regions = identity.list_region_subscriptions( config["tenancy"] ).data

      self.compartments.append( oci.identity.models.Compartment(compartment_id=tenancy.id, name=f'{tenancy.name} (root)', description=tenancy.description, id=tenancy.id) )
      self.compartments += identity.list_compartments( config["tenancy"], compartment_id_in_subtree=True, access_level="ACCESSIBLE" ).data

      for region in self.regions:
         config["region"] = region.region_name
         identity = oci.identity.IdentityClient(config)

         self.availability_domains += identity.list_availability_domains(config['tenancy']).data

   def get_compartments(self):
      return [c for c in self.compartments if ( c.lifecycle_state == 'ACTIVE' and c.name != 'ManagedCompartmentForPaaS' and c.name != 'OCI_Scripts' )]

   def get_availability_domains( self, region_name):
      #return [e for e in availability.domains if e.region_name == region_name]
      data = []
      for ad in self.availability_domains:
         s = ad.name.split( '-')
         name = f'{s[0][5:].lower()}-{s[1].lower()}-{s[2].lower()}'
         if name == region_name.lower():
            data.append( ad )

      return data

   def print(self):
      # Tenancy
      #print( 'tenancy_id, tenancy_name, description, home_region')
      #print( f'{self.tenancy_id}, {self.name}, {self.description}, {self.home_region}')

      data = 'tenancy_id, tenancy_name, description, home_region, report_no'
      data += '\n'
      data += f'{self.tenancy_id}, {self.name}, {self.description}, {self.home_region}, {report_no}'

      write_file( data, 'tenancy' )

      # Region

      # print( 'tenancy_id, region_key, region_name, is_home_region, report_no')
      # for region in self.regions:
      #    print( f'{self.tenancy_id}, {region.region_key}, {region.region_name}, {region.is_home_region}, {report_no}')
      data = 'tenancy_id, region_key, region_name, is_home_region, report_no'
      
      for region in self.regions:
         data += '\n'
         data += f'{self.tenancy_id}, {region.region_key}, {region.region_name}, {region.is_home_region}, {report_no}'
      
      write_file( data, 'region' )

      # Compartment
      # print( 'compartment_id, name, description, tenancy_id, report_no')
      # for compartment in self.compartments:
      #    print( f'{compartment.id}, {compartment.name}, {compartment.description}, {compartment.compartment_id}, {report_no}')

      data = 'compartment_id, name, description, tenancy_id, report_no'      

      for compartment in self.compartments:
         data += '\n'
         data += f'{compartment.id}, {compartment.name}, {compartment.description}, {compartment.compartment_id}, {report_no}'

      write_file( data, 'compartment' )

      # Availability Domains
      # print( 'ad_id, ad_name, tenancy_id, region_name')
      # for ad in self.availability_domains:
      #    s = ad.name.split( '-')
      #    print( f'{ad.id}, {ad.name}, {ad.compartment_id}, {s[0][5:].lower()}-{s[1].lower()}-{s[2].lower()}')

      data = 'ad_id, ad_name, tenancy_id, region_name, report_no'
      for ad in self.availability_domains:
         s = ad.name.split( '-')
         data += '\n'
         data += f'{ad.id}, {ad.name}, {ad.compartment_id}, {s[0][5:].lower()}-{s[1].lower()}-{s[2].lower()}, {report_no}'

      write_file( data, 'availability_domain' )
class Announcement(object):
   annoucements = []

   def __init__(self, config):
      announcement_service = oci.announcements_service.AnnouncementClient( config )
      self.announcements = announcement_service.list_announcements( config[ "tenancy" ], lifecycle_state=oci.announcements_service.models.AnnouncementSummary.LIFECYCLE_STATE_ACTIVE, sort_by="timeCreated" ).data

   def print(self):
      # print( 'affected_regions, announcement_type, announcement id, reference_ticket_number, services, summary, time_updated, type' )

      # for announcement in self.announcements.items:
      #    affected_regions = str(announcement.affected_regions).strip( '[]' ).replace( ',', '/' ).replace( "'",'' )
      #    services = str(announcement.services).strip( '[]' ).replace( ',', '/' ).replace( "'",'' )
      #    print( f'{affected_regions}, {announcement.announcement_type}, {announcement.id}, {announcement.reference_ticket_number}, {services}, {announcement.summary}, {announcement.time_updated}, {announcement.type}' )    

      data = 'affected_regions, announcement_type, announcement id, reference_ticket_number, services, summary, time_updated, type, report_no'

      for announcement in self.announcements.items:
         affected_regions = str(announcement.affected_regions).strip( '[]' ).replace( ',', '/' ).replace( "'",'' )
         services = str(announcement.services).strip( '[]' ).replace( ',', '/' ).replace( "'",'' )
         data += '\n'
         data += f'{affected_regions}, {announcement.announcement_type}, {announcement.id}, {announcement.reference_ticket_number}, {services}, {announcement.summary}, {announcement.time_updated}, {announcement.type}, {report_no}'
      
      write_file( data, 'announcement' )

class Limit(object):

   limit_summary = []

   def __init__(self, config, tenancy):
      tenancy_id = config[ "tenancy" ]

      for region in tenancy.regions:
         config[ 'region'] = region.region_name
         
         limits_client = oci.limits.LimitsClient(config)
         
         services = limits_client.list_services( tenancy_id, sort_by="name").data

         if services:
            # oci.limits.models.ServiceSummary
            for service in services:            
               # get the limits per service
               
               limits = limits_client.list_limit_values(tenancy_id, service_name=service.name, sort_by="name").data

               for limit in limits:
                  val = {
                           'service_name': str(service.name),
                           'service_description': str(service.description),
                           'limit_name': str(limit.name),
                           'availability_domain': ("" if limit.availability_domain is None else str(limit.availability_domain)),
                           'scope_type': str(limit.scope_type),
                           'value': str(limit.value),
                           'used': "",
                           'available': "",
                           'region_name': str(config['region'])
                  }

                  # if not limit, continue, don't calculate limit = 0
                  if limit.value == 0:
                     continue

                  # get usage per limit if available
                  usage = []
                  
                  if limit.scope_type == "AD":
                     usage = limits_client.get_resource_availability(service.name, limit.name, tenancy_id, availability_domain=limit.availability_domain).data
                  else:
                     usage = limits_client.get_resource_availability(service.name, limit.name, tenancy_id).data

                  # oci.limits.models.ResourceAvailability
                  if usage.used:
                     val['used'] = str(usage.used)
                     
                  if usage.available:
                     val['available'] = str(usage.available)

                  self.limit_summary.append(val)

   def print(self):
      # print( 'region_name, service_name, service_description, limit_name, availability_domain, scope_type, value, used, available' )
      # for limit in self.limit_summary:
      #    print( f"{limit['region_name']}, {limit['service_name']}, {limit['service_description']}, {limit['limit_name']}, {limit['availability_domain']}, {limit['scope_type']}, {limit['value']}, {limit[ 'used' ]}, {limit[ 'available' ]}" )

      data = 'region_name, service_name, service_description, limit_name, availability_domain, scope_type, value, used, available, report_no'
      for limit in self.limit_summary:
         data += '\n'
         data += f"{limit['region_name']}, {limit['service_name']}, {limit['service_description']}, {limit['limit_name']}, {limit['availability_domain']}, {limit['scope_type']}, {limit['value']}, {limit[ 'used' ]}, {limit[ 'available' ]}, {report_no}"

      write_file( data, 'limit' )

class Compute(object):
   dedicated_hosts = []
   instances = []
   bv_attachments = []
   vol_attachments = []
   tenancy_id = None

   def __init__(self, config, tenancy):
      self.tenancy_id = config[ 'tenancy']

      for region in tenancy.regions:
         config[ 'region'] = region.region_name

         compute_client = oci.core.ComputeClient(config)

         for c in tenancy.get_compartments():
            self.dedicated_hosts += compute_client.list_dedicated_vm_hosts(c.id).data
            self.instances += compute_client.list_instances(c.id).data
            self.vol_attachments += compute_client.list_volume_attachments(c.id).data

            ads = tenancy.get_availability_domains(region.region_name)

            for ad in ads:
               self.bv_attachments += compute_client.list_boot_volume_attachments( ad.name, c.id ).data
               
   def print(self):
      # Print Dedicated VM Hosts
      # print( 'id, availability_domain, compartment_id, dedicated_vm_host_shape, display_name, fault_domain, lifecycle_state, remaining_ocpus, total_ocpus' )
      # for host in self.dedicated_hosts:
      #     print( f'{host.id}, {host.availability_domain}, {host.compartment_id}, {host.dedicated_vm_host_shape}, {host.display_name}, {host.fault_domain}, {host.lifecycle_state}, {host.remaining_ocpus}, {host.total_ocpus}' )

      data = 'id, availability_domain, compartment_id, dedicated_vm_host_shape, display_name, fault_domain, lifecycle_state, remaining_ocpus, total_ocpus, report_no'
      for host in self.dedicated_hosts:
         data += '\n'
         data += f'{host.id}, {host.availability_domain}, {host.compartment_id}, {host.dedicated_vm_host_shape}, {host.display_name}, {host.fault_domain}, {host.lifecycle_state}, {host.remaining_ocpus}, {host.total_ocpus}, {report_no}'

      write_file( data, 'dedicated_vm_host' )

      # Print VM Instances
      # print( 'instance_id, availability_domain, compartment_id, dedicated_vm_host_id, display_name, fault_domain, lifecycle_state, region, shape, tenancy_id' )
      # for instance in self.instances:
      #     print( f'{instance.id}, {instance.availability_domain}, {instance.compartment_id}, {instance.dedicated_vm_host_id}, {instance.display_name}, {instance.fault_domain}, {instance.lifecycle_state}, {instance.region}, {instance.shape}, {self.tenancy_id}' )

      data = 'instance_id, availability_domain, compartment_id, dedicated_vm_host_id, display_name, fault_domain, lifecycle_state, region, shape, tenancy_id, report_no'
      for instance in self.instances:
         data += '\n'
         data += f'{instance.id}, {instance.availability_domain}, {instance.compartment_id}, {instance.dedicated_vm_host_id}, {instance.display_name}, {instance.fault_domain}, {instance.lifecycle_state}, {instance.region}, {instance.shape}, {self.tenancy_id}, {report_no}'

      write_file( data, 'instance' )

      # Print Boot Volume Attachments
      # print( 'id, availability_domain, boot_volume_id, compartment_id, display_name, instance_id, is_pv_encryption_in_transit_enabled, lifecycle_state' )
      # for bv in self.bv_attachments:
      #     print( f'{bv.id}, {bv.availability_domain}, {bv.boot_volume_id}, {bv.compartment_id}, {bv.display_name}, {bv.instance_id}, {bv.is_pv_encryption_in_transit_enabled}, {bv.lifecycle_state}' )

      data = 'id, availability_domain, boot_volume_id, compartment_id, display_name, instance_id, is_pv_encryption_in_transit_enabled, lifecycle_state, report_no'
      for bv in self.bv_attachments:
         data += '\n'
         data += f'{bv.id}, {bv.availability_domain}, {bv.boot_volume_id}, {bv.compartment_id}, {bv.display_name}, {bv.instance_id}, {bv.is_pv_encryption_in_transit_enabled}, {bv.lifecycle_state}, {report_no}'

      write_file( data, 'bv_attachment' )

      # Print Volume Attachments
      # print( 'id, attachment_type, availability_domain, compartment_id, device, display_name, instance_id, is_pv_encryption_in_transit_enabled, is_read_only, is_shareable, lifecycle_state, volume_id' )
      # for vol in self.vol_attachments:
      #     print( f'{vol.id}, {vol.attachment_type}, {vol.availability_domain}, {vol.compartment_id}, {vol.device}, {vol.display_name}, {vol.instance_id}, {vol.is_pv_encryption_in_transit_enabled}, {vol.is_read_only}, {vol.is_shareable}, {vol.lifecycle_state}, {vol.volume_id}' )

      data = 'id, attachment_type, availability_domain, compartment_id, device, display_name, instance_id, is_pv_encryption_in_transit_enabled, is_read_only, is_shareable, lifecycle_state, volume_id, report_no'
      for vol in self.vol_attachments:
         data += '\n'
         data += f'{vol.id}, {vol.attachment_type}, {vol.availability_domain}, {vol.compartment_id}, {vol.device}, {vol.display_name}, {vol.instance_id}, {vol.is_pv_encryption_in_transit_enabled}, {vol.is_read_only}, {vol.is_shareable}, {vol.lifecycle_state}, {vol.volume_id}, {report_no}'
         write_file( data, 'vol_attachment' )

class BootVolume(object):
   boot_volumes = []

   def __init__(self, config, tenancy):

      for region in tenancy.regions:
         config[ 'region'] = region.region_name
         
         identity = oci.identity.IdentityClient(config)
         block_storage_client = oci.core.BlockstorageClient(config)

         cnt = 0
         
         for c in tenancy.get_compartments():                   
            ads = tenancy.get_availability_domains(region.region_name)

            for ad in ads:            
               self.boot_volumes += block_storage_client.list_boot_volumes(ad.name, c.id).data

               cnt += 1
               # sleep 0.5 seconds every 10 checks to avoid too many requests
               if cnt % 5 == 0:
                  time.sleep(0.5)

   def print(self):
      # print( 'id, availability_domain, compartment_id, display_name, image_id, is_hydrated, kms_key_id, lifecycle_state, size_in_gbs, size_in_mbs, volume_group_id, vpus_per_gb' )
      # for bv in self.boot_volumes:
      #    print( f'{bv.id}, {bv.availability_domain}, {bv.compartment_id}, {bv.display_name}, {bv.image_id}, {bv.is_hydrated}, {bv.kms_key_id}, {bv.lifecycle_state}, {bv.size_in_gbs}, {bv.size_in_mbs}, {bv.volume_group_id}, {bv.vpus_per_gb}' )

      data = 'id, availability_domain, compartment_id, display_name, image_id, is_hydrated, kms_key_id, lifecycle_state, size_in_gbs, size_in_mbs, volume_group_id, vpus_per_gb, report_no'
      for bv in self.boot_volumes:
         data += '\n'
         data = f'{bv.id}, {bv.availability_domain}, {bv.compartment_id}, {bv.display_name}, {bv.image_id}, {bv.is_hydrated}, {bv.kms_key_id}, {bv.lifecycle_state}, {bv.size_in_gbs}, {bv.size_in_mbs}, {bv.volume_group_id}, {bv.vpus_per_gb}, {report_no}'

      write_file( data, 'boot_volume' )

class BlockVolume(object):
   block_volumes = []

   def __init__(self, config, tenancy):

      for region in tenancy.regions:
         config[ 'region'] = region.region_name
         
         block_storage_client = oci.core.BlockstorageClient(config)

         cnt = 0

         for c in tenancy.get_compartments():                                 
            self.block_volumes += block_storage_client.list_volumes(c.id).data

            cnt += 1
            # sleep 0.5 seconds every 10 checks to avoid too many requests
            if cnt % 5 == 0:
               time.sleep(0.5)

   def print(self):      
      # print( 'id, availability_domain, compartment_id, display_name, is_hydrated, kms_key_id, lifecycle_state, size_in_gbs, size_in_mbs, volume_group_id, vpus_per_gb' )
      # for bv in self.block_volumes:
      #    print( f'{bv.id}, {bv.availability_domain}, {bv.compartment_id}, {bv.display_name}, {bv.is_hydrated}, {bv.kms_key_id}, {bv.lifecycle_state}, {bv.size_in_gbs}, {bv.size_in_mbs}, {bv.volume_group_id}, {bv.vpus_per_gb}' )

      data = 'id, availability_domain, compartment_id, display_name, is_hydrated, kms_key_id, lifecycle_state, size_in_gbs, size_in_mbs, volume_group_id, vpus_per_gb, report_no'
      for bv in self.block_volumes:
         data += '\n'
         data += f'{bv.id}, {bv.availability_domain}, {bv.compartment_id}, {bv.display_name}, {bv.is_hydrated}, {bv.kms_key_id}, {bv.lifecycle_state}, {bv.size_in_gbs}, {bv.size_in_mbs}, {bv.volume_group_id}, {bv.vpus_per_gb}, {report_no}'

      write_file( data, 'block_volume' )

class DBSystem(object):
   db_systems = []
   db_homes = []
   databases = []
   dg_associations = []
   autonomous_exadata = []
   autonomous_cdb = []
   autonomous_db = []

   def __init__(self, config, tenancy):
      
      for region in tenancy.regions:
         config['region'] = region.region_name

         db_client = oci.database.DatabaseClient(config)

         for c in tenancy.get_compartments():           
            self.db_systems += db_client.list_db_systems(c.id).data

            db_homes = db_client.list_db_homes(c.id).data
            self.db_homes += db_homes

            for db_home in db_homes:
               self.databases += db_client.list_databases(c.id, db_home_id=db_home.id).data
            
            # for db in databases:
            #    self.dg_associations += db_client.list_data_guard_associations(db.id).data             
           
            self.autonomous_exadata += db_client.list_autonomous_exadata_infrastructures(c.id).data
            
            self.autonomous_cdb += db_client.list_autonomous_container_databases(c.id).data

            self.autonomous_db += db_client.list_autonomous_databases( c.id ).data

   def print(self):
      # Print DB System
      # print( 'id, availability_domain, cluster_name, compartment_id, cpu_core_count, data_storage_percentage, data_storage_size_in_gbs, database_edition, disk_redundancy, display_name, domain, hostname, lifecycle_state, node_count, reco_storage_size_in_gb, shape, sparse_diskgroup, version')
      # for db_system in self.db_systems:
      #    print( f'{db_system.id}, {db_system.availability_domain}, {db_system.cluster_name}, {db_system.compartment_id}, {db_system.cpu_core_count}, {db_system.data_storage_percentage}, {db_system.data_storage_size_in_gbs}, {db_system.database_edition}, {db_system.disk_redundancy}, {db_system.display_name}, {db_system.domain}, {db_system.hostname}, {db_system.lifecycle_state}, {db_system.node_count}, {db_system.reco_storage_size_in_gb}, {db_system.shape}, {db_system.sparse_diskgroup}, {db_system.version}' )

      data = 'id, availability_domain, cluster_name, compartment_id, cpu_core_count, data_storage_percentage, data_storage_size_in_gbs, database_edition, disk_redundancy, display_name, domain, hostname, lifecycle_state, node_count, reco_storage_size_in_gb, shape, sparse_diskgroup, version, report_no'
      for db_system in self.db_systems:
         data += '\n'
         data += f'{db_system.id}, {db_system.availability_domain}, {db_system.cluster_name}, {db_system.compartment_id}, {db_system.cpu_core_count}, {db_system.data_storage_percentage}, {db_system.data_storage_size_in_gbs}, {db_system.database_edition}, {db_system.disk_redundancy}, {db_system.display_name}, {db_system.domain}, {db_system.hostname}, {db_system.lifecycle_state}, {db_system.node_count}, {db_system.reco_storage_size_in_gb}, {db_system.shape}, {db_system.sparse_diskgroup}, {db_system.version}, {report_no}'
      
      write_file( data, 'db_system' )

      # Print DB Home
      # print( 'id, compartment_id, db_system_id, db_version, display_name, last_patch_history_entry_id, lifecycle_state' )     
      # for db_home in self.db_homes:
      #    print( f'{db_home.id}, {db_home.compartment_id}, {db_home.db_system_id}, {db_home.db_version}, {db_home.display_name}, {db_home.last_patch_history_entry_id}, {db_home.lifecycle_state}' )

      data = 'id, compartment_id, db_system_id, db_version, display_name, last_patch_history_entry_id, lifecycle_state, report_no'
      for db_home in self.db_homes:
         data += '\n'
         data += f'{db_home.id}, {db_home.compartment_id}, {db_home.db_system_id}, {db_home.db_version}, {db_home.display_name}, {db_home.last_patch_history_entry_id}, {db_home.lifecycle_state}, {report_no}'

      write_file( data, 'db_home' )
      
      # Print Database
      # print( 'id, compartment_id, auto_backup_enabled, auto_backup_window, backup_destination_details, recovery_window_in_days, db_home_id, db_name, db_unique_name, db_workload, lifecycle_state, pdb_name' )
      # for db in self.databases:
      #    print( f'{db.id}, {db.compartment_id}, {db.db_backup_config.auto_backup_enabled}, {db.db_backup_config.auto_backup_window}, {db.db_backup_config.backup_destination_details}, {db.db_backup_config.recovery_window_in_days}, {db.db_home_id}, {db.db_name}, {db.db_unique_name}, {db.db_workload}, {db.lifecycle_state}, {db.pdb_name}' )

      data = 'id, compartment_id, auto_backup_enabled, auto_backup_window, backup_destination_details, recovery_window_in_days, db_home_id, db_name, db_unique_name, db_workload, lifecycle_state, pdb_name, report_no'
      for db in self.databases:
         data += '\n'
         data += f'{db.id}, {db.compartment_id}, {db.db_backup_config.auto_backup_enabled}, {db.db_backup_config.auto_backup_window}, {db.db_backup_config.backup_destination_details}, {db.db_backup_config.recovery_window_in_days}, {db.db_home_id}, {db.db_name}, {db.db_unique_name}, {db.db_workload}, {db.lifecycle_state}, {db.pdb_name}, {report_no}'

      write_file( data, 'database' )

      # # Print DG Association
      # print( '' )

      # for db in self.databases:
      #    print( f'' )

      # Print Autonomous Exadata
      # print( 'id, availability_domain, compartment_id, display_name, domain, hostname, last_maintenance_run_id, license_model, lifecycle_state, maintenance_window, next_maintenance_run_id, shape' )
      # for auto_exadata in self.autonomous_exadata:
      #    print( f'{auto_exadata.id}, {auto_exadata.availability_domain}, {auto_exadata.compartment_id}, {auto_exadata.display_name}, {auto_exadata.domain}, {auto_exadata.hostname}, {auto_exadata.last_maintenance_run_id}, {auto_exadata.license_model}, {auto_exadata.lifecycle_state}, {auto_exadata.maintenance_window}, {auto_exadata.next_maintenance_run_id}, {auto_exadata.shape}' )

      data = 'id, availability_domain, compartment_id, display_name, domain, hostname, last_maintenance_run_id, license_model, lifecycle_state, maintenance_window, next_maintenance_run_id, shape, report_no'
      for auto_exadata in self.autonomous_exadata:
         data += '\n'
         data += f'{auto_exadata.id}, {auto_exadata.availability_domain}, {auto_exadata.compartment_id}, {auto_exadata.display_name}, {auto_exadata.domain}, {auto_exadata.hostname}, {auto_exadata.last_maintenance_run_id}, {auto_exadata.license_model}, {auto_exadata.lifecycle_state}, {auto_exadata.maintenance_window}, {auto_exadata.next_maintenance_run_id}, {auto_exadata.shape}, {report_no}'

      write_file( data, 'autonomous_exadata' )

      # Print Autonomous Container DB
      # print( 'id, autonomous_exadata_infrastructure_id, availability_domain, backup_config, compartment_id, display_name, last_maintenance_run_id, lifecycle_state, maintenance_window, next_maintenance_run_id, patch_model, service_level_agreement_type' )
      # for acdb in self.autonomous_cdb:
      #    print( f'{acdb.id}, {acdb.autonomous_exadata_infrastructure_id}, {acdb.availability_domain}, {acdb.backup_config}, {acdb.compartment_id}, {acdb.display_name}, {acdb.last_maintenance_run_id}, {acdb.lifecycle_state}, {acdb.maintenance_window}, {acdb.next_maintenance_run_id}, {acdb.patch_model}, {acdb.service_level_agreement_type}' )
      
      data = 'id, autonomous_exadata_infrastructure_id, availability_domain, backup_config, compartment_id, display_name, last_maintenance_run_id, lifecycle_state, maintenance_window, next_maintenance_run_id, patch_model, service_level_agreement_type, report_no'
      for acdb in self.autonomous_cdb:
         data += '\n'
         data += f'{acdb.id}, {acdb.autonomous_exadata_infrastructure_id}, {acdb.availability_domain}, {acdb.backup_config}, {acdb.compartment_id}, {acdb.display_name}, {acdb.last_maintenance_run_id}, {acdb.lifecycle_state}, {acdb.maintenance_window}, {acdb.next_maintenance_run_id}, {acdb.patch_model}, {acdb.service_level_agreement_type}, {report_no}'

      write_file( data, 'autonomous_cdb' )

      # Print Autonomous DB
      # print( 'id, autonomous_container_database_id, compartment_id, cpu_core_count, data_safe_status, data_storage_size_in_tbs, db_name, db_version, db_workload, display_name, is_auto_scaling_enabled, is_dedicated, is_free_tier, lifecycle_state, whitelisted_ips' )
      # for adb in self.autonomous_db:
      #    print( f'{adb.id}, {adb.autonomous_container_database_id}, {adb.compartment_id}, {adb.cpu_core_count}, {adb.data_safe_status},  {adb.data_storage_size_in_tbs}, {adb.db_name}, {adb.db_version}, {adb.db_workload}, {adb.display_name}, {adb.is_auto_scaling_enabled}, {adb.is_dedicated}, {adb.is_free_tier}, {adb.lifecycle_state}, {adb.whitelisted_ips}' )
      
      data = 'id, autonomous_container_database_id, compartment_id, cpu_core_count, data_safe_status, data_storage_size_in_tbs, db_name, db_version, db_workload, display_name, is_auto_scaling_enabled, is_dedicated, is_free_tier, lifecycle_state, whitelisted_ips, report_no'
      for adb in self.autonomous_db:
         data += '\n'
         data += f'{adb.id}, {adb.autonomous_container_database_id}, {adb.compartment_id}, {adb.cpu_core_count}, {adb.data_safe_status},  {adb.data_storage_size_in_tbs}, {adb.db_name}, {adb.db_version}, {adb.db_workload}, {adb.display_name}, {adb.is_auto_scaling_enabled}, {adb.is_dedicated}, {adb.is_free_tier}, {adb.lifecycle_state}, {adb.whitelisted_ips}, {report_no}'

      write_file( data, 'autonomous_db' )

def write_file( strdata, filename ):
   global report_no
   global par_url

   resp = requests.put( f'{par_url}{filename}_{report_no}.csv', data=strdata.encode('utf-8'))
   print( f'{par_url}{filename}_{report_no}.csv - file written')
   print( resp )
