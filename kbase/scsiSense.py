
"""
Brief:
    scsiSense.py - Contains scsiSense class definition

Description: -
    This file provides SCSI Sense information
    
Class(es):
    Enter GetHeaders("kbase\\scsiSense") to display Class listings.

Function(s):
    None

Related: -

Author(s):
    Ofer Levy, Farzana Akhter
"""

import __init__
import os
import re
from util.utility import dumpbuf
from twidl_os import getRoot


keyinfo = {
            0x00:'No Sense',
            0x01:'Recovered Error',
            0x02:'Not Ready',
            0x03:'Medium Error',
            0x04:'Hardware Error',
            0x05:'Illegal Request',
            0x06:'Unit Attention',
            0x07:'Data Protect',
            0x08:'Not Used',
            0x09:'Vendor Specific',
            0x0A:'Not Used',
            0x0B:'Aborted Command',
            0x0E:'Other',
            }



# Codes can be found here...
# http://www.t10.org/lists/asc-num.htm

#Category    Key    ASC     ASCQ     Error Condition
kcqinfo = \
{
#No Sense
    (0x0,     0x00,     0x00):   'No error',
    (0x0,     0x5D,     0x00):   'No sense - PFA threshold reached',
#Soft Error
    (0x1,     0x01,     0x00):   'Recovered Write error - no index',
    (0x1,     0x02,     0x00):   'Recovered no seek completion',
    (0x1,     0x03,     0x00):   'Recovered Write error - write fault',
    (0x1,     0x09,     0x00):   'Track following error',
    (0x1,     0x0B,     0x01):   'Temperature warning',
    (0x1,     0x0C,     0x01):   'Recovered Write error with auto-realloc - reallocated',
    (0x1,     0x0C,     0x03):   'Recovered Write error - recommend reassign',
    (0x1,     0x12,     0x01):   'Recovered data without ECC using prev logical block ID',
    (0x1,     0x12,     0x02):   'Recovered data with ECC using prev logical block ID',
    (0x1,     0x14,     0x01):   'Recovered Record Not Found',
    (0x1,     0x16,     0x00):   'Recovered Write error - Data Sync Mark Error',
    (0x1,     0x16,     0x01):   'Recovered Write error - Data Sync Error - data rewritten',
    (0x1,     0x16,     0x02):   'Recovered Write error - Data Sync Error - recommend rewrite',
    (0x1,     0x16,     0x03):   'Recovered Write error - Data Sync Error - data auto-reallocated',
    (0x1,     0x16,     0x04):   'Recovered Write error - Data Sync Error - recommend reassignment',
    (0x1,     0x17,     0x00):   'Recovered data with no error correction applied',
    (0x1,     0x17,     0x01):   'Recovered Read error - with retries',
    (0x1,     0x17,     0x02):   'Recovered data using positive offset',
    (0x1,     0x17,     0x03):   'Recovered data using negative offset',
    (0x1,     0x17,     0x05):   'Recovered data using previous logical block ID',
    (0x1,     0x17,     0x06):   'Recovered Read error - without ECC, auto reallocated',
    (0x1,     0x17,     0x07):   'Recovered Read error - without ECC, recommend reassign',
    (0x1,     0x17,     0x08):   'Recovered Read error - without ECC, recommend rewrite',
    (0x1,     0x17,     0x09):   'Recovered Read error - without ECC, data rewritten',
    (0x1,     0x18,     0x00):   'Recovered Read error - with ECC',
    (0x1,     0x18,     0x01):   'Recovered data with ECC and retries',
    (0x1,     0x18,     0x02):   'Recovered Read error - with ECC, auto reallocated',
    (0x1,     0x18,     0x05):   'Recovered Read error - with ECC, recommend reassign',
    (0x1,     0x18,     0x06):   'Recovered data using ECC and offsets',
    (0x1,     0x18,     0x07):   'Recovered Read error - with ECC, data rewritten',
    (0x1,     0x1C,     0x00):   'Defect List not found',
    (0x1,     0x1C,     0x01):   'Primary defect list not found',
    (0x1,     0x1C,     0x02):   'Grown defect list not found',
    (0x1,     0x1F,     0x00):   'Partial defect list transferred',
    (0x1,     0x44,     0x00):   'Internal target failure',
    (0x1,     0x5D,     0x00):   'PFA threshold reached',
#Not Ready
    (0x2,     0x04,     0x00):   'Cause not reportable',
    (0x2,     0x04,     0x01):   'becoming ready',
    (0x2,     0x04,     0x02):   'need initialise command (start unit)',
    (0x2,     0x04,     0x03):   'Nmanual intervention required',
    (0x2,     0x04,     0x04):   'format in progress',
    (0x2,     0x04,     0x09):   'self-test in progress',
    (0x2,     0x31,     0x00):   'medium format corrupted',
    (0x2,     0x31,     0x01):   'format command failed',
    (0x2,     0x35,     0x02):   'enclosure services unavailable',
    (0x2,     0x4C,     0x00):   'Diagnostic Failure - config not loaded',
#Medium Error
    (0x3,     0x03,     0x00):   'write fault',
    (0x3,     0x10,     0x00):   'ID CRC error',
    (0x3,     0x11,     0x00):   'unrecovered read error',
    (0x3,     0x11,     0x01):   'read retries exhausted',
    (0x3,     0x11,     0x02):   'error too long to correct',
    (0x3,     0x11,     0x04):   'unrecovered read error - auto re-alloc failed',
    (0x3,     0x11,     0x0B):   'unrecovered read error - recommend reassign',
    (0x3,     0x14,     0x01):   'record not found',
    (0x3,     0x16,     0x00):   'Data Sync Mark error',
    (0x3,     0x16,     0x04):   'Data Sync Error - recommend reassign',
    (0x3,     0x19,     0x00):   'defect list error',
    (0x3,     0x19,     0x01):   'defect list not available',
    (0x3,     0x19,     0x02):   'defect list error in primary list',
    (0x3,     0x19,     0x03):   'defect list error in grown list',
    (0x3,     0x19,     0x0E):   'fewer than 50% defect list copies',
    (0x3,     0x31,     0x00):   'medium format corrupted',
    (0x3,     0x31,     0x01):   'format command failed',
#Hardware Error
    (0x4,     0x01,     0x00):   'no index or sector',
    (0x4,     0x02,     0x00):   'no seek complete',
    (0x4,     0x03,     0x00):   'write fault',
    (0x4,     0x09,     0x00):   'track following error',
    (0x4,     0x11,     0x00):   'unrecovered read error in reserved area',
    (0x4,     0x16,     0x00):   'Data Sync Mark error in reserved area',
    (0x4,     0x19,     0x00):   'defect list error',
    (0x4,     0x19,     0x02):   'defect list error in Primary List',
    (0x4,     0x19,     0x03):   'defect list error in Grown List',
    (0x4,     0x31,     0x00):   'reassign failed',
    (0x4,     0x32,     0x00):   'no defect spare available',
    (0x4,     0x35,     0x01):   'unsupported enclosure function',
    (0x4,     0x35,     0x02):   'enclosure services unavailable',
    (0x4,     0x35,     0x03):   'enclosure services transfer failure',
    (0x4,     0x35,     0x04):   'enclosure services refused',
    (0x4,     0x35,     0x05):   'enclosure services checksum error',
    (0x4,     0x3E,     0x03):   'self-test failed',
    (0x4,     0x3E,     0x04):   'unable to update self-test',
    (0x4,     0x44,     0x00):   'internal target failure',
#Illegal Request
    (0x5,     0x1A,     0x00):   'parm list length error',
    (0x5,     0x20,     0x00):   'invalid/unsupported command code',

# Added specific ASC value's for 0x20/0x21/0x22 - Drew Knerr
    (0x5,     0x20,     0x01):   'ACCESS DENIED - INITIATOR PENDING-ENROLLED',
    (0x5,     0x20,     0x02):   'ACCESS DENIED - NO ACCESS RIGHTS',
    (0x5,     0x20,     0x03):   'ACCESS DENIED - INVALID MGMT ID KEY',
    (0x5,     0x20,     0x04):   'ILLEGAL COMMAND WHILE IN WRITE CAPABLE STATE',
    (0x5,     0x20,     0x05):   'Obsolete',
    (0x5,     0x20,     0x06):   'ILLEGAL COMMAND WHILE IN EXPLICIT ADDRESS MODE',
    (0x5,     0x20,     0x07):   'ILLEGAL COMMAND WHILE IN IMPLICIT ADDRESS MODE',
    (0x5,     0x20,     0x08):   'ACCESS DENIED - ENROLLMENT CONFLICT',
    (0x5,     0x20,     0x09):   'ACCESS DENIED - INVALID LU IDENTIFIER',
    (0x5,     0x20,     0x0A):   'ACCESS DENIED - INVALID PROXY TOKEN',
    (0x5,     0x20,     0x0B):   'ACCESS DENIED - ACL LUN CONFLICT',
    (0x5,     0x20,     0x0C):   'ILLEGAL COMMAND WHEN NOT IN APPEND-ONLY MODE',

    (0x5,     0x21,     0x00):   'LBA out of range',
    (0x5,     0x21,     0x01):   'INVALID ELEMENT ADDRESS',
    (0x5,     0x21,     0x02):   'INVALID ADDRESS FOR WRITE',
    (0x5,     0x21,     0x03):   'INVALID WRITE CROSSING LAYER JUMP',
    (0x5,     0x21,     0x04):   'UNALIGNED WRITE COMMAND',
    (0x5,     0x21,     0x05):   'WRITE BOUNDARY VIOLATION',
    (0x5,     0x21,     0x06):   'ATTEMPT TO READ INVALID DATA',
    (0x5,     0x21,     0x07):   'READ BOUNDARY VIOLATION',

    (0x5,     0x22,     0x00):   'ILLEGAL FUNCTION (USE 20 00, 24 00, OR 26 00)',


    
    (0x5,     0x24,     0x00):   'invalid field in CDB (Command Descriptor Block)',
    (0x5,     0x25,     0x00):   'invalid LUN',
    (0x5,     0x26,     0x00):   'invalid fields in parm list',
    (0x5,     0x26,     0x01):   'parameter not supported',
    (0x5,     0x26,     0x02):   'invalid parm value',
    (0x5,     0x26,     0x03):   'invalid field parameter - threshold parameter',
    (0x5,     0x26,     0x04):   'invalid release of persistent reservation',
    (0x5,     0x2C,     0x00):   'command sequence error',
    (0x5,     0x35,     0x01):   'unsupported enclosure function',
    (0x5,     0x49,     0x00):   'invalid message',
    (0x5,     0x53,     0x00):   'media load or eject failed',
    (0x5,     0x53,     0x01):   'unload tape failure',
    (0x5,     0x53,     0x02):   'medium removal prevented',
    (0x5,     0x55,     0x00):   'system resource failure',
    (0x5,     0x55,     0x01):   'system buffer full',
    (0x5,     0x55,     0x04):   'Insufficient Registration Resources',
#Unit Attention     
    (0x6,     0x28,     0x00):   'not-ready to ready transition (format complete)',
    (0x6,     0x29,     0x00):   'power on, device reset or bus device reset occurred',
    (0x6,     0x29,     0x01):   'power on occurred',
    (0x6,     0x29,     0x02):   'SCSI bus reset occurred',
    (0x6,     0x29,     0x03):   'TARGET RESET occurred',
    (0x6,     0x29,     0x04):   ' self-initiated-reset occurred',
    (0x6,     0x29,     0x05):   'transceiver mode change to SE',
    (0x6,     0x29,     0x06):   'transceiver mode change to LVD',
    (0x6,     0x2A,     0x00):   'parameters changed',
    (0x6,     0x2A,     0x01):   'mode parameters changed',
    (0x6,     0x2A,     0x02):   'log select parms changed',
    (0x6,     0x2A,     0x03):   'Reservations pre-empted',
    (0x6,     0x2A,     0x04):   'Reservations released',
    (0x6,     0x2A,     0x05):   'Registrations pre-empted',
    (0x6,     0x2F,     0x00):   'commands cleared by another initiator',
    (0x6,     0x3F,     0x00):   'target operating conditions have changed',
    (0x6,     0x3F,     0x01):   'microcode changed',
    (0x6,     0x30,     0x02):   'changed operating definition',
    (0x6,     0x3F,     0x03):   'inquiry parameters changed',
    (0x6,     0x3F,     0x05):   'device identifier changed',
    (0x6,     0x5D,     0x00):   'PFA threshold reached',
#Write Protect
    (0x7,     0x20,     0x01):   'access denied - initiator pending-enrolled',
    (0x7,     0x20,     0x02):   'access denied - no access rights',
    (0x7,     0x20,     0x03):   'access denied - invalid mgmt id key',
    (0x7,     0x20,     0x04):   'illegal command while in write capable state',
    (0x7,     0x20,     0x05):   'obsolete',
    (0x7,     0x20,     0x06):   'illegal command while in explicit address mode',
    (0x7,     0x20,     0x07):   'illegal command while in implicit address mode',
    (0x7,     0x20,     0x08):   'access denied - enrollment conflict',
    (0x7,     0x20,     0x09):   'access denied - invalid lu identifier',
    (0x7,     0x20,     0x0a):   'access denied - invalid proxy token',
    (0x7,     0x20,     0x0b):   'access denied - acl lun conflict',
    (0x7,     0x20,     0x0c):   'illegal command when not in append-only mode',
    (0x7,     0x27,     0x00):   'command not allowed',
#Aborted Command
    (0xB,     0x00,     0x00):   'no additional sense code',
    (0xB,     0x1B,     0x00):   'sync data transfer error (extra ACK)',
    (0xB,     0x25,     0x00):   'unsupported LUN',
    (0xB,     0x3F,     0x0F):   'echo buffer overwritten',
    (0xB,     0x43,     0x00):   'message reject error',
    (0xB,     0x44,     0x00):   'internal target failure',
    (0xB,     0x45,     0x00):   'Selection/Reselection failure',
    (0xB,     0x47,     0x00):   'SCSI parity error',
    (0xB,     0x48,     0x00):   'initiator-detected error message received',
    (0xB,     0x49,     0x00):   'inappropriate/illegal message',
    (0xB,     0x4B,     0x00):   'data phase error',
    (0xB,     0x4E,     0x00):   'overlapped commands attempted',
    (0xB,     0x4F,     0x00):   'due to loop initialisation',
#Other
    (0xE,     0x1D,     0x00):   'Miscompare - during verify byte check operation',
    ('x',     0x05,     0x00):   'Illegal request',
    ('x',     0x06,     0x00):   'Unit attention',
    ('x',     0x07,     0x00):   'Data protect',
    ('x',     0x08,     0x00):   'LUN communication failure',
    ('x',     0x08,     0x01):   'LUN communication timeout',
    ('x',     0x08,     0x02):   'LUN communication parity error',
    ('x',     0x08,     0x03):   'LUN communication CRC error',
    ('x',     0x09,     0x00):   'vendor specific sense key',
    ('x',     0x09,     0x01):   'servo fault',
    ('x',     0x09,     0x04):   'head select fault',
    ('x',     0x0A,     0x00):   'error log overflow',
    ('x',     0x0B,     0x00):   'aborted command',
    ('x',     0x0C,     0x00):   'write error',
    ('x',     0x0C,     0x02):   'write error - auto-realloc failed',
    ('x',     0x0E,     0x00):   'data miscompare',
    ('x',     0x12,     0x00):   'address mark not founf for ID field',
    ('x',     0x14,     0x00):   'logical block not found',
    ('x',     0x15,     0x00):   'random positioning error',
    ('x',     0x15,     0x01):   'mechanical positioning error',
    ('x',     0x15,     0x02):   'positioning error detected by read of medium',
    ('x',     0x27,     0x00):   'write protected',
    ('x',     0x29,     0x00):   'power on or bus reset occurred',
    ('x',     0x31,     0x01):   'format failed',
    ('x',     0x32,     0x01):   'defect list update error',
    ('x',     0x32,     0x02):   'no spares available',
    ('x',     0x35,     0x01):   'unspecified enclosure services failure',
    ('x',     0x37,     0x00):   'parameter rounded',
    ('x',     0x3D,     0x00):   'invalid bits in identify message',
    ('x',     0x3E,     0x00):   'LUN not self-configured yet',
    ('x',     0x40,     0x01):   'DRAM parity error',
    ('x',     0x40,     0x02):   'DRAM parity error',
    ('x',     0x42,     0x00):   'power-on or self-test failure',
    ('x',     0x4C,     0x00):   'LUN failed self-configuration',
    ('x',     0x5C,     0x00):   'RPL status change',
    ('x',     0x5C,     0x01):   'spindles synchronised',
    ('x',     0x5C,     0x02):   'spindles not synchronised',
    ('x',     0x65,     0x00):   'voltage fault',
#    (x     >=80     x)     Vendor specific
#    (x     x     >=80)     Vendor specific
}

# SCSI sense key constants for key,code and qualifier indexes within the sens buffer
# Sense key index, Additional sense code index, additional sense code qualifier index
RESPONSE_CODE_IDX = 0
SK_IDX      = 2 
ASC_IDX     = 12 
ASCQ_IDX    = 13
               

class ScsiSense():
    """
    Brief: 
        ScsiSense() - SCSISense Class
    
    Description:
            
    Class(es):
        None
    
    Method(s):
       Enter GetHeaders("kbase.ScsiSense") to display Method listings.
    
    Related: -
    
    Author(s): 
        Farzana Akhter
       
    """
    
    @staticmethod
    def createDictionary():
        """
        Brief:
            createDictionary() - Load the UEC Eureka definition into a dictionary.

        Description: -

        Argument(s):
            None

        Return Value(s):
            UEC Dictionary

        Example:
            ScsiSense.createDictionary()

        Related: -

        Author(s):
            Arpit Patel, Farzana Akhter
            
        """
        uecDictionary = {}
        pattern = re.compile('[a-fA-F0-9]')   
        
        try:
            filePointer = open(os.path.join(getRoot(), 'kbase', 'uec_eureka.txt'), 'r')
            filePointer.readline()
            filePointer.readline()
            filePointer.readline()
            filePointer.readline()
            tuple = ""
            s = ""
            for line in filePointer:
                tuple = line.partition(" ")
                if(pattern.match(tuple[0]) != None):
                    valueKey = int(tuple[0],16)
                    uecDictionary[valueKey] = tuple[2]
            filePointer.close()

        except IOError as ex:
            print ex
        
        return uecDictionary  
        
    @staticmethod            
    def getErrorDescription(sense):
        """
        Brief: 
            getErrorDescription(sense) - Returns Error description by decoding bytes 20-21
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            Returns Error description by decoding bytes 20-21
        
        Example: 
            ScsiSense.getErrorDescription(getLastSense()) -> 'NO_ERROR'
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        if len(sense) > 21:
            uecDictionary = ScsiSense.createDictionary()
            uec = (sense[20] << 8) | (sense[21])
            if uec in uecDictionary:
                return uecDictionary[uec].strip()
            else:
                return None
        else:
            return None
        
    @staticmethod    
    def getSenseKeyDescription(sense):
        """
        Brief: 
            getSenseKeyDescription(sense) - Returns sense key description by decoding bit 0-3 on byte 2
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            Returns sense key description by decoding bit 0-3 on byte 2
        
        Example: 
            ScsiSense.getSenseKeyDescription(getLastSense()) -> 'No Sense'
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        if len(sense) > 2:
            SenseKey = sense[2] & 0x0F
            if keyinfo.has_key(SenseKey):
                return keyinfo[SenseKey]
            else:
                return None
        else:
            return None
        
    @staticmethod    
    def getLBA(sense):
        """
        Brief: 
            getLBA(sense) - Returns LBA if valid bit is 1 and ILI bit is 0. Returns Residue if valid bit is 1 and ILI is 1.
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            Returns LBA if valid bit is 1 and ILI bit is 0. Returns Residue if valid bit is 1 and ILI is 1.
        
        Example: 
            lba = ScsiSense.getLBA(getLastSense())
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        lba = None
        valid = ScsiSense.getValid(sense)
        if valid == 1: 
            ILI = (sense[2] >> 5) & 0x01
            if ILI == 0:
                lba = (sense [3] << 24 ) | (sense [4] << 16 ) | (sense [5] << 8 ) | sense [6] 
            else: # ILL = 1 Therefore bytes 3-6 are the "Residue" of requested length in bytes
                lba = 0
        return lba
    
    @staticmethod
    def getValid(sense):
        """
        Brief: 
            getValid(sense) - Prints if Information bytes 3-6 contain valid/invalid LBA
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            Returns valid bit value (bit 7 on byte 0)
        
        Example: 
            validbit = ScsiSense.getValid(getLastSense())
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        ValidBit = 0
        if len(sense) > 0:
            ValidBit = (sense[0] >> 7) & 0x01
            if ValidBit == 0:
                print "bytes 3-6 contain an invalid LBA"
            else:
                print "bytes 3-6 contain a valid LBA"
        return ValidBit
  
    @staticmethod    
    def getErrorCode(sense):
        """
        Brief: 
            getErrorCode(sense) - Prints Error code (bit 0-6 on Byte 0)
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            Returns Error code value (bit 0-6 on Byte 0)
        
        Example: 
            errCode = ScsiSense.getErrorCode (getLastSense())
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        
        ErrorCode = 0
        if len(sense) > 0:
            ErrorCode = sense[0] & 0x7F
            if ErrorCode == 0x70:
                print "Current Error"
            elif ErrorCode == 0x71:
                print "Deferred Error"
        return ErrorCode       

    @staticmethod
    def printSense(sense ):    
        """
        Brief: 
            printSense(sense) - Prints translation of the sense data(key,code,qualifier) in 'sense' buffer
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                    
        Return Value(s): 
            None
        
        Example: 
            ScsiSense.printSense (getLastSense())
        
        Related: -
        
        Author(s): 
            Ofer Levy
            
        """
        if sense != None:
            
            key, asc, ascq =  sense[SK_IDX]& 0x0F , sense[ASC_IDX], sense[ASCQ_IDX]
            
            if ( ScsiSense.getErrorCode(sense) in (0x70,0x71) ):   
                if keyinfo.has_key(key):
                    keystring = keyinfo[key]
                else:
                    keystring = 'Unknown Key: %d'%(key)
                
                kcq_tupple = (key,asc,ascq)
                kcq_alternate_tupple = ('x',asc,ascq)
                
                if kcqinfo.has_key(kcq_tupple):
                    kcqstring = kcqinfo[kcq_tupple]
                elif  kcqinfo.has_key(kcq_alternate_tupple):
                    kcqstring = kcqinfo[kcq_alternate_tupple]
                else:
                   kcqstring = 'Unknown Key/ASC/ASCQ: %s'%(str(kcq_tupple))
                   dumpbuf( sense, len(sense) )
                
                print keystring + ' - ' + kcqstring      
        
    @staticmethod
    def isPowerOnCondition(sense ):
        """
        Brief: 
            isPowerOnCondition(sense) - Return true if power on conditioned occurred
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
        
        Return Value(s): 
            True if power on conditioned occurred, otherwise False
        
        Example: 
            ScsiSense.isPowerOnCondition(getLastSense()) -> True
        
        Related: -
        
        Author(s): 
            Ofer Levy
            
        """
        if len(sense) > ASCQ_IDX:
            return( not sense[SK_IDX]&0x0F or ((6==sense[SK_IDX]&0x0F) and 0x29==sense[ASC_IDX] and 1 >= sense[ASCQ_IDX]) )
        else:
            return False
    
    @staticmethod
    def getUEC(sense):       
        """
        Brief: 
            getUEC(sense) - Returns UEC code for SCSI device at fault
        
        Description: -
            This is a static method
            
        Argument(s): 
            sense - (Required) scsi sense data
                   
        Return Value(s): 
            Returns UEC code if device at fault, None otherwise
        
        Example: 
            ScsiSense.getUEC (getLastSense())
        
        Related: -
        
        Author(s): 
            Farzana Akhter
            
        """
        if len(sense) > 21:
            uecDictionary = ScsiSense.createDictionary()
            uecCode = (sense[20] << 8) | (sense[21])
            if uecCode in uecDictionary and uecCode != 0x0:               
                return uecCode
        return None

