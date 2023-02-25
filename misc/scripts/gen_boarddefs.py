#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import json

@dataclass
class ChipInfo:
    name: str
    flash_kb: int
    sram_kb: int
    freq_mhz: int
    package: str

    def get_classification_macro(self) -> Optional[str]:
        # I don't have a good answer for that except
        # copying the data from the reference manual
        # (CH32FV2x_V3xRM-1.pdf p.4)
        dev_classes = {
            "CH32F20x_D6": ["CH32F203K8", "CH32F203C6", "CH32F203C8"],
            "CH32F20x_D8": ["CH32F203CB", "CH32F203RC", "CH32F203VC", "CH32F203RB"],
            "CH32F20x_D8C": ["CH32F205RB", "CH32F207VC"],
            "CH32F20x_D8W": ["CH32F208RB", "CH32F208WB"],
            "CH32V20x_D6": ["CH32V203F6", "CH32V203G6", "CH32V203K6", "CH32V203F8", "CH32V203G8", "CH32V203K8", "CH32V203C6", "CH32V203C8"],
            "CH32V20x_D8": ["CH32V203RB"],
            "CH32V20x_D8W": ["CH32V208GB", "CH32V208CB", "CH32V208RB", "CH32V208WB"],
            "CH32V30x_D8": ["CH32V303CB", "CH32V303RB", "CH32V303RC", "CH32V303VC"],
            "CH32V30x_D8C": ["CH32V305FB", "CH32V305RB", "CH32V307RC", "CH32V307WC", "CH32V307VC"]
        }
        for dev_class, devs in dev_classes.items():
            if any([self.name.upper().startswith(chip) for chip in devs]):
                return dev_class
        # the V103 series intentionally has no classification macro
        if self.name.upper().startswith("CH32V103"):
            return None
        print("ERROR: UNKNOWN CHIP / NO CLASSIFICATION KNOWN FOR " + self.name)
        exit(-1)

    def get_riscv_arch_and_abi(self) -> Tuple[str, str]:
        # ch32v30x is capable of rv32imafcxw
        # but SDK uses rv32imacxw (no floating point)
        # ch32v208 is rv32imacxw (QingKe V4C)
        # other ch32v20x is rv32imacxw (QingKe V4B)
        # ch32v10x only rv32imac (RISC-V3A)
        # ch32v00x only rv32ecxw (RISC-V2A)
        if self.name.lower().startswith("ch32v3"):
            return ("rv32imacxw", "ilp32")
        elif self.name.lower().startswith("ch32v2"):
            return ("rv32imacxw", "ilp32")
        elif self.name.lower().startswith("ch32v1"):
            return ("rv32imac", "ilp32")
        elif self.name.lower().startswith("ch32v0"):
            return ("rv32ecxw", "ilp32e")
        else:
            print("ERROR: UNKNOWN CHIP ABI/ARCH FOR " + self.name)
            exit(-1)
            return ("unknown", "unknown")

    def chip_without_package(self) -> str:
        return self.name[:-2]

    def exact_series(self) -> str:
        return self.name[0:len("ch32vxxx")]

chip_db: List[ChipInfo] = [
    # CH32V103
    ChipInfo("CH32V103C6T6", 32, 10, 72, "LQFP48"),
    ChipInfo("CH32V103C8U6", 64, 20, 72, "QFN48"),
    ChipInfo("CH32V103C8T6", 64, 20, 72, "LQFP48"),
    ChipInfo("CH32V103R8T6", 64, 20, 72, "LQFP64M"),
    # CH32V203
    ChipInfo("CH32V203F6T6", 32, 10, 144, "TSSOP20"),
    ChipInfo("CH32V203F8P6", 64, 20, 144, "TSSOP20"),
    ChipInfo("CH32V203F8U6", 64, 20, 144, "QFN20X3"),
    ChipInfo("CH32V203G6U6", 32, 10, 144, "QFN28X4"),
    ChipInfo("CH32V203G8R6", 64, 20, 144, "QSOP28"),
    ChipInfo("CH32V203K6T6", 32, 10, 144, "LQFP32"),
    ChipInfo("CH32V203K8T6", 64, 20, 144, "LQFP32"),
    ChipInfo("CH32V203C6T6", 32, 10, 144, "LQFP48"),
    ChipInfo("CH32V203C8T6", 64, 20, 144, "LQFP48"),
    ChipInfo("CH32V203C8U6", 64, 20, 144, "QFN48X7"),
    ChipInfo("CH32V203RBT6", 128, 64, 144, "LQFP64M"),
    # CH32V208
    ChipInfo("CH32V208GBU6", 128, 64, 144, "QFN28X4"),
    ChipInfo("CH32V208CBU6", 128, 64, 144, "QFN48X5"),
    ChipInfo("CH32V208RBT6", 128, 64, 144, "LQFP64M"),
    ChipInfo("CH32V208WBU6", 128, 64, 144, "QFN68X8"),
    # CH32V30x
    ChipInfo("CH32V303CBT6", 128, 32, 144, "LQFP58"),
    ChipInfo("CH32V303RBT6", 128, 32, 144, "LQFP64M"),
    ChipInfo("CH32V303RCT6", 256, 64, 144, "LQFP64M"),
    ChipInfo("CH32V303VCT6", 256, 64, 144, "LQFP100"),
    ChipInfo("CH32V305FBP6", 128, 32, 144, "TSSOP20"),
    ChipInfo("CH32V305RBT6", 128, 32, 144, "LQFP64M"),
    ChipInfo("CH32V307RCT6", 256, 64, 144, "LQFP64M"),
    ChipInfo("CH32V307WCU6", 256, 64, 144, "QFN64X8"),
    ChipInfo("CH32V307VCT6", 256, 64, 144, "LQFP100"),
]

def get_chip(name: str) -> Optional[ChipInfo]:
    for c in chip_db:
        if c.name.lower() == name.lower():
            return c
    return None

@dataclass
class KnownBoard:
    file_name: str
    board_name: str
    chip: ChipInfo
    url: str
    vendor: str
    add_info: Optional[Dict[str, Any]] = None

known_boards: List[KnownBoard] = [
    KnownBoard("ch32v307_evt", "CH32V307 EVT", get_chip("CH32V307VCT6"),
               "https://www.tindie.com/products/adz1122/ch32v307v-evt-r1-risc-v-development-board/", "SCDZ")
]

def create_board_json(info: ChipInfo, board_name:str, output_path: str, patch_info: Optional[Dict[str, Any]] = None, addtl_extra_flags:List[str] = None):
    arch, abi = info.get_riscv_arch_and_abi()
    base_json = {
        "build": {
            "f_cpu": str(info.freq_mhz * 1000_000) + "L",
            "extra_flags": "",
            "hwids": [
                [
                    "0x1A86",
                    "0x8010"
                ]
            ],
            "mabi": abi,
            "march": arch,
            "mcu": info.name.lower()
        },
        "debug": {
            "onboard_tools": [
                "wch-link"
            ],
            "openocd_config": "wch-riscv.cfg",
            "svd_path": info.exact_series().upper() + "xx.svd"
        },
        "frameworks": [
            "noneos-sdk"
        ],
        "name": board_name,
        "upload": {
            "maximum_ram_size": info.sram_kb * 1024,
            "maximum_size": info.flash_kb * 1024,
            "protocols": [
                "wch-link"
            ],
            "protocol": "wch-link"
        },
        "url": f"http://www.wch-ic.com/products/{info.exact_series().upper()}.html",
        "vendor": "W.CH"
    }
    # add some classification macros
    extra_flags = [
        f"-D{info.chip_without_package()}", 
        f"-D{info.name[0:len('ch32vxx')]}X",
        f"-D{info.name[0:len('ch32vxxx')]}",
    ]
    classification_macro = info.get_classification_macro()
    if classification_macro is not None:
        extra_flags += ["-D" + classification_macro]
    if addtl_extra_flags is not None:
        extra_flags.extend(addtl_extra_flags)
    base_json["build"]["extra_flags"] = " ".join(extra_flags)
    if patch_info is not None:
        for k, v in patch_info.items():
            # upmost level
            if k.count(".") == 0:
                base_json[k] = v
            # one deeper (e.g. build.extra_flags)
            if k.count(".") == 1:
                k1, k2 = k.split(".")
                base_json[k1][k2] = v
    as_str = json.dumps(base_json, indent=2)
    print("DEFINITION FOR %s:\n%s" % (board_name, as_str))
    try:
        Path(output_path).write_text(as_str, encoding='utf-8')
    except Exception as exc:
        print("Error writing board definition: %s" % repr(exc))


def main():
    # generate board JSON for all known chips directly into boards folder
    base_path = Path(__file__).parents[2].resolve() / "boards"
    # all generic chips first
    for info in chip_db:
        output_path = base_path / f"generic{info.name.upper()}.json"
        name = f"Generic {info.name.upper()}"
        create_board_json(info, name, output_path)
        #return
    # all known boards now
    for known_board in known_boards:
        output_path = base_path / f"{known_board.file_name}.json"
        create_board_json(known_board.chip, known_board.board_name, output_path, {
                          "url": known_board.url, "vendor": known_board.vendor})
    pass


if __name__ == '__main__':
    main()