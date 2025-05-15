class PyIndi():
    """
    Checkout indiapi.h and indibasetypes.h
    """
    # ISState
    ISS_OFF = 0
    ISS_ON = 0

    # IPState
    IPS_IDLE = 0
    IPS_OK = 1
    IPS_BUSY = 2
    IPS_ALERT = 3

    # ISRule
    ISR_1OFMANY = 0
    ISR_ATMOST1 = 1
    ISR_NOFMANY = 2

    # IPerm
    IP_RO = 0
    IP_WO = 1
    IP_RW = 2

    # INDI_PROPERTY_TYPE
    INDI_NUMBER = 0
    INDI_SWITCH = 1
    INDI_TEXT = 2
    INDI_LIGHT = 3
    INDI_BLOB = 4
    INDI_UNKNOWN = 5

    # INDI_BLOB_MODE
    B_NEVER = 0
    B_ALSO = 1
    B_ONLY = 2

    BlobModeMapper = {
        0: "Never",
        1: "Also",
        2: "Only"
    }