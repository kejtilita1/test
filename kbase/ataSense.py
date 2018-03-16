"""
Brief:
    ataSense.py - Contains ataSense class definition

Description: -
    This file translate ATA specification for Status and Error
    
Class(es):
    Enter GetHeaders("kbase\\ataSense") to display Class listings.

Function(s):
    None

Related: -

Author(s):
    Ofer Levy, Farzana Akhter
"""

import __init__

#Status register
#Bit   Description
#15:8  Reserved
#7:6   Transport Dependent
#5     Device Fault
#4     N/A
#3     Transport Dependent
#2     N/A
#1     N/A
#0     Error - This bit is set if any of the error register bits are set

#Error register
#Bit   Description
#15:8  Reserved
#7     Interface CRC
#6     Uncorrectable
#5     Obsolete
#4     ID Not Found
#3     Obsolete
#2     Abort
#1     Obsolete
#0     Obsolete

# Status register

#Status = \
#{
#    0:"Error (ERR) - The Error bit in the status field shall be set to one if\
#       any bit in the Error field (see 6.2) is set to one",
#    1:"N/A",
#    2:"N/A",
#    3:"N/A",    
#    4:"Data Request (DRQ) - Status bit 4. This bit is transport dependent. \
#       Refer to the appropriate transport standard for the usage of this bit.",
#       #6.1.6 Deferred Write Error (DWE)
#       #Status bit 4. DWE shall be set to one if an error was detected in a deferred write to the media for a previous
#       #WRITE STREAM DMA EXT or WRITE STREAM EXT command. This error is from a previously issued
#       #command. If DWE is set to one, the location of the deferred error is only reported in the Write Stream error log.
#       #
#       #6.1.7 Service (SERV)
#       #Status bit 4. SERV shall be cleared to zero when no other queued command is ready for service. SERV shall be
#       #set to one when another queued command is ready for service. SERV shall be set to one when the device has
#       #prepared this command for service. If TCQ is not supported, this bit is command specific.
#    5:"Device Fault (DF) - If the device enters a condition where continued \
#       operation could affect user data integrity, the device shall set the DF\
#       bit in the status field and no longer accept commands. This condition is\
#       only cleared by power cycling the drive. Once the DF bit has been cleared\
#       it may remain clear until a command that could affect user data integrity\
#       is received by the device. Examples of conditions that may cause the DF \
#       bit to be set by a device are: Failure to spin-up properly, and no spares\
#       remaining for reallocation.",     
#       #Status bit 5. SE is set to one if an error occurred during the processing of a command in the Streaming feature
#       #set and either Read Continuous (RC) is set to one in a READ STREAM command (see 7.36.3.3) or Write
#       #Continuous (WC) is set to one in a WRITE STREAM command (see 7.73.3.2). When SE is set to one, the value
#       #returned in the LBA bits (47:0) contains the address of the first logical sector in error, and the Count field contains
#       #the number of consecutive logical sectors that may contain errors. If RC is set to one in a READ STREAM
#       #command or WC is set to one a WRITE STREAM command, and ICRC, UNC, IDNF, ABRT, or CCTO is set to
#       #one (see 6.3), then the SE bit is set to one, the ERR bit is cleared to zero, and the error information (e.g., bits set
#       #in the Error field) are saved in the appropriate Read Stream or Write Stream Error log.       
#    6:"Device Ready (DRDY)",
#    7:"Busy (BSY) - This bit is transport dependent. Refer to the applicable\
#       transport standard for the usage of this bit."
#       #6.1.9 Transport Dependent (TD)
#       #ATA/ATAPI-7 defines the status bits BSY,DRDY, and DRQ. This bits are documented in the transport standards.
#       #Although all of the commands in this standard use BSY=0, DRDY=1 and DRQ=0 to specify that the device is
#       #ready to accept a command and to specify that a command is complete, they are processed differently in the
#       #various transport standard.
#}

Error = \
{
    0:"Command Completion Time Out (CCTO) - Error bit 0. CCTO shall be set to one if a \nCommand Completion Time Limit Out error has occurred.",
       #6.2.5 Illegal Length Indicator (ILI)
       #Error bit 0. The operation of this bit is specific to the SCSI command set implemented by ATAPI devices.
       #6.2.7 Media Error (MED)
       #Error bit 0. Media Error shall be set to one if a media error is detected.
       #6.2.11 Attempted partial range removal
       #Error bit 0. The command attempted to unpin part of a previously defined command range.
       #6.2.12 Insufficient NV Cache space
       #Error bit 0. There is not enough NV Cache to satisfy the NV Cache command       
    1:"End of Media (EOM) - Error bit 1. The operation of this bit is specific to the \n  SCSI command set implemented by ATAPI devices.",
       #6.2.13 Insufficient LBA Range Entries remaining
       #Error bit 1. The device has run out of space to store LBA ranges for NV Cache commands.     
    2:"Abort (ABRT) - Error bit 2. Abort shall be set to one if the command is not supported.\n  Abort may be set to one if the device is not able to complete the action requested by \n  the command. Abort shall also be set to one if an address outside of the range of \n  user-accessible addresses is requested if IDNF is not set to one.",
    3:"N/A",
    4:"ID Not Found (IDNF) - Error bit 4. ID Not Found shall be set to one if a \n  user-accessible address could not be found. ID Not Found shall be set to one \n  if an address outside of the range of user-accessible addresses is requested \n  when command aborted is not returned.",
       #6.2.8 Sense Key
       #Error bits (7:4) The operation of this four bit field is specific to the
       #SCSI command set implemented by ATAPI devices.
    5:"N/A",       
    6:"Uncorrectable Error (UNC) - Uncorrectable Error shall be set to one if\n  data is uncorrectable.",
       #6.2.10 Write Protect (WP)
       #Error bit 6. Write Protect shall be set to one for each execution of GET
       #MEDIA STATUS while the media is write protected.
    7:"Interface CRC (ICRC) - Error bit 7. Interface CRC shall be set to one if an \n  interface CRC error has occurred during an Ultra DMA data transfer. The content \n  of this bit may be applicable to Multiword DMA and PIO data transfers."
}

uecDictionary = \
{
    0xF620: "UEC_SOUTH_ENABLE_LOGICAL",                       # context loaded clean
    0xF621: "UEC_SOUTH_DISABLE_LOGICAL_NO_CONTEXT",           # south found no context
    0xF622: "UEC_SOUTH_DISABLE_LOGICAL_BAD_CONTEXT",          # south found a context, but it was bad
    0xF623: "UEC_SOUTH_DISABLE_LOGICAL_ASSERTED",             # south is asserted
    0xF624: "UEC_SOUTH_DISABLE_LOGICAL_NO_DEFECT_MAP",        # south found no defect map
    0xF625: "UEC_SOUTH_DISABLE_LOGICAL_NO_SPACE",             # south found no space
    0xF626: "UEC_SOUTH_DISABLE_LOGICAL_CHAN_CE_CONFLICT",     # south found a slot conflict during discovery
    0xF627: "UEC_SOUTH_READ_ONLY",                            # south is in read-only
    0xF628: "UEC_SOUTH_LOG_INVALID",                          # south is in disable logical state and cannot return requested log
    0xF629: "UEC_SOUTH_NAND_DISCOVERY_ERROR",                 # south had trouble discovering its NAND.
    0xF630: "UEC_SOUTH_GENERIC_BOOT_ERROR",                   # generic catch-all for other boot errors
    0xF631: "UEC_SOUTH_NO_FW",                                # South firmware has no fw and in bootloader.
    0xF632: "UEC_SOUTH_INVALID_FW",                           # South firmware has invalid firmware
    0xF633: "UEC_SOUTH_NO_SLOW_CTX",                          # South firmware cannot find slow ctx   
    0xF634: "UEC_SOUTH_BAD_SLOW_CTX",                         # South firmware slow context found with no defect map or 0-length defect map   
    0xF635: "UEC_SOUTH_NO_SPACE",                             # South firmware does not have enough DRAM to create/load L2P_R table for configured capacity
    0xF636: "UEC_SOUTH_OBSOLETE_NAND",                        # South firmware discovery failed due to illegal geometry/NAND
    0xF637: "UEC_SOUTH_NO_MFG_DATA",                          # South firmware device forced into MFG mode, no persistent data found  
    0xF638: "UEC_SOUTH_BAD_DRAM",                             # South firmware device failed sdram test
    0xF639: "UEC_SOUTH_BAD_NORTH_FW",                         # South firmware device indicates we had issues loading the North FW
    0xF63A: "UEC_SOUTH_DISABLE_LOGICAL_BAD_DEFECT_MAP",       # South found invalid defect map   
    0xF63B: "UEC_SOUTH_NO_CONTEXT_MISMATCH_DIE_MAPPING_VER",  # South fast context fail, context find mismatch die mapping version
}

#6.3 Interrupt Reason Bits
#6.3.1 Command/Data (C/D)
#Count bit 0. Shall be set to zero if the transfer is data, otherwise C/D shall be set to one.
#6.3.2 Input/Output (I/O)
#Count bit 1. Shall be cleared to zero if the transfer is to the device (O). Shall be set to one if the transfer is to the
#host (I).
#6.3.3 Release (REL)
#Count bit 2. Shall be set to one if a command has been accepted but not completed and the device is ready to
#accept another command.
#December 11, 2006 T13/1699-D Revision 3f
#Working Draft AT Attachment 8 - ATA/ATAPI Command Set (ATA8-ACS) 55
#6.3.4 Tag
#Count bits (7:3). If the device supports TCQ, this field contains the Tag value for the command. A Tag value may
#be any value between 0 and 31 regardless of the queue depth supported.
#T13/1699-D Revision 3f December 11, 2006
#56 Working

# index in the ATA TF where the Status byte is located
STATUS_IDX = 6
# Index in the ATA TF where the Error byte is located
ERROR_IDX  = 0
              

class AtaSense():
    """
    Brief: 
        AtaSense() - AtaSense Class
    
    Description:       
    
    Class(es):
        None
    
    Method(s):       
         Enter GetHeaders("kbase.AtaSense") to display Method listings.
         
    Related: -
    
    Author(s): 
        Ofer Levy, Farzana Akhter
       
    """              
    
    @staticmethod
    def printSense(sense):       
        """
        Brief: 
            printSense(sense) - Prints ATA Error translation if any
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) ata sense data
                   
        Return Value(s): 
            None
        
        Example: 
            AtaSense.printSense (getLastSense())
        
        Related: -
        
        Author(s): 
            Ofer Levy, Farzana Akhter
            
        """
        if sense != None and len(sense) > 0 and len(sense[0]) == 8:
            if ( sense[0][STATUS_IDX] & 0x1 ):
                retStr, error = "", sense[0][ERROR_IDX]
                print "Drive Error: Status", hex(sense[0][STATUS_IDX]), ", Error:",hex(sense[0][ERROR_IDX]), "\n"
    
                for i in range(8):
                    if (1<<i & error):
                        retStr += Error[i]
        
                print retStr, "\n"
        else:
            print "NO_SENSE_DATA" 
                    
    @staticmethod
    def getErrorDescription(sense):       
        """
        Brief: 
            getErrorDescription(sense) - Prints ATA Error Code description
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) ata sense data
                   
        Return Value(s): 
            Returns Error description
        
        Example: 
           AtaSense.getErrorDescription (getLastSense()) -> 'NO_ERROR'
        
        Related: -
        
        Author(s): 
            Ofer Levy, Farzana Akhter
            
        """
        
        if len(sense) > 0 and len(sense[0]) == 8:
            if ( sense[0][STATUS_IDX] & 0x1 ):     
                retStr, error = "", sense[0][ERROR_IDX]       
                for i in range(8):
                    if (1<<i & error):
                        retStr += Error[i]
        
                return retStr, "\n" 
            else:
                return "NO_ERROR"
        else:
            return "NO_SENSE_DATA"
        
    @staticmethod
    def getUEC(sense):       
        """
        Brief: 
            getUEC(sense) - Returns UEC code for ATA device at fault
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) ata sense data
                   
        Return Value(s): 
            Returns UEC code if device at fault, None otherwise
        
        Example: 
            AtaSense.getUEC (getLastSense())
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        
        if len(sense) > 0 and len(sense[0]) == 8:
            if ( sense[0][4] == 0x06 ):
                uecCode = (sense[1][4] << 8) | (sense[1][3])           
                if uecCode in uecDictionary:                    
                    return uecCode
        return None

