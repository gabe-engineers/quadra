from enum import Enum


class EndpointCreateInputDataCenterIdsItem(str, Enum):
    AP_IN_1 = "AP-IN-1"
    AP_JP_1 = "AP-JP-1"
    CA_MTL_1 = "CA-MTL-1"
    CA_MTL_2 = "CA-MTL-2"
    CA_MTL_3 = "CA-MTL-3"
    EUR_IS_1 = "EUR-IS-1"
    EUR_IS_2 = "EUR-IS-2"
    EUR_IS_3 = "EUR-IS-3"
    EUR_NO_1 = "EUR-NO-1"
    EU_CZ_1 = "EU-CZ-1"
    EU_FR_1 = "EU-FR-1"
    EU_NL_1 = "EU-NL-1"
    EU_RO_1 = "EU-RO-1"
    EU_SE_1 = "EU-SE-1"
    OC_AU_1 = "OC-AU-1"
    US_CA_2 = "US-CA-2"
    US_DE_1 = "US-DE-1"
    US_GA_1 = "US-GA-1"
    US_GA_2 = "US-GA-2"
    US_IL_1 = "US-IL-1"
    US_KS_2 = "US-KS-2"
    US_KS_3 = "US-KS-3"
    US_MD_1 = "US-MD-1"
    US_NC_1 = "US-NC-1"
    US_TX_1 = "US-TX-1"
    US_TX_3 = "US-TX-3"
    US_TX_4 = "US-TX-4"
    US_WA_1 = "US-WA-1"

    def __str__(self) -> str:
        return str(self.value)
