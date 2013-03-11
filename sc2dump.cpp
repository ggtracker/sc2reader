/* Dump type ids for Units and Abils for SC2.
 *
 * Authors: Robert Nix (@mischanix), Graylin Kim (@GraylinKim)
 *
 * Must be linked with the Microsoft Version.lib library. If compiling on 32 bit you may require the LAA option.
 *
 * Usage: sc2dump.exe <UNIT_DATA_OUTPUT> <ABIL_DATA_OUTPUT>
 * Example:
 *
 *  $ sc2dump.exe 24764/units.csv 24764/abils.csv
 *  Searching for a live SC2 process.
 *
 *  Found SC2.exe
 *      Path: C:\Program Files (x86)\StarCraft II 2012 Beta\Versions\Base24764\SC2.exe
 *      Base Address: 590000
 *      Build: 24764
 *
 *  Dumping Catalog@0x7903b54
 *      Dumping CAbil@0x790b7f4 to 24764/24764_abils.csv
 *      Dumping CUnit@0x791f864 to 24764/24764_units.csv
 *
 *  Done.
 *
 * If the script can't find the SC2 process or the offset is bad it will tell you. If SC2 is running an
 * unknown offset you'll need to use CheatEngine to find a new one and make a new case for the switch
 * statement.
 *
 * For Heart of the Swarm:
 *  1. Attach to the process 
 *  2. Make sure that writable is unchecked and executable is fully checked
 *  3. Do an array search for "8b 0d ?? ?? ?? ?? 8b 49"
 *  4. Look for the most common match.
 *  5. The the ?? ?? ?? ?? portion is the bytes in reverse order for the gameCatalog
 *  6. Subtract the base address for the process (which you can get by running this script)
 *  7. Add a new case for this build with that information. cUnitIndex and stringNameOffset generally won't change
 *
 * For Wings of Liberty:
 * 1. Use the "a1 ?? ?? ?? ?? 8b 80" search string with the HotS instructions above.
 *
 */
#include <Windows.h>
#include <psapi.h>
#include <TlHelp32.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>

const int MAX_PROC_NAME_SIZE = 512;
const int MAX_PROC_LIST_SIZE = 2048;

void DumpIds(HANDLE sc2_handle, uint32_t catalogRecordList, uint32_t stringNameOffset, FILE* out);
uint32_t ReadUInt(uint32_t address, HANDLE sc2_handle);
char* ReadString(uint32_t address, uint32_t length, HANDLE sc2_handle);
uint32_t GetModuleBase(DWORD, char *);

HANDLE getSC2Handle();
char* getSC2Info(HANDLE sc2_handle, uint32_t &base_address, uint32_t &build);

int main(int argc, char* argv[]) {
	if (argc < 3) {
		printf("Both unit and ability output files are required (in that order).\n");
		ExitProcess(1);
	}
	
	char* units_filename = argv[1];
	char* abils_filename = argv[2];

	
	printf("Searching for a live SC2 process.\n");
	HANDLE sc2_handle = getSC2Handle();
	if (sc2_handle == NULL) {
		printf("Error: SC2.exe not found\n");
		ExitProcess(1);
	}
	
	uint32_t build;
	uint32_t base_address;
	char* sc2_exe_path = getSC2Info(sc2_handle, base_address, build);
	if (sc2_exe_path == NULL) {
		printf("Error: Unable to acquire base address and build information.\n");
		ExitProcess(1);
	} else {
		printf("\nFound SC2.exe\n");
		printf("  Path: %s\n", sc2_exe_path);
		printf("  Base Address: %x\n", base_address);
		printf("  Build: %d\n", build);
	}

	uint32_t gameCatalog = 0;
	uint32_t cUnitIndex = 0;
	uint32_t stringNameOffset = 0;
	switch(build) {
		case 23260: // WoL 1.5.3.23260
			gameCatalog = 0x1362BA0u;
			cUnitIndex = 0x110u;
			stringNameOffset = 0x64u;
			break;
		case 23925: // HotS beta 2.0.0.23925
			gameCatalog = 0x1EA2BE8u;
			cUnitIndex = 0x110u;
			stringNameOffset = 0x40u;
			break;
		case 24247: // HotS beta 2.0.0.24247
			gameCatalog = 0x10C9B28u;
			cUnitIndex = 0x11cu;
			stringNameOffset = 0x40u;
			break;
		case 24764: // HotS beta 2.0.3.24764
			gameCatalog = 0x10E79B8u;
			cUnitIndex = 0x11cu;
			stringNameOffset = 0x40u;
			break;
		default:
			printf("Error: Missing offset values for build %d\n",build);
			ExitProcess(1);
	}
	
	uint32_t gameCatalogTable = ReadUInt(base_address + gameCatalog,sc2_handle);
	printf("\nDumping Catalog@0x%x\n", gameCatalogTable);

	FILE* abils_file;
	if (fopen_s(&abils_file,abils_filename, "w")==0) {
		uint32_t abilCatalogList = ReadUInt(gameCatalogTable + 0x1c,sc2_handle);
		printf("  Dumping CAbil@0x%x to %s\n", abilCatalogList, abils_filename);
		DumpIds(sc2_handle, abilCatalogList, stringNameOffset, abils_file);
		fclose(abils_file);
	} else {
		printf("  ERROR: Could not open %s for writing.",abils_filename);
	}

	FILE* units_file;
	if (fopen_s(&units_file, units_filename , "w")==0) {
		uint32_t unitCatalogList = ReadUInt(gameCatalogTable + cUnitIndex,sc2_handle);
		printf("  Dumping CUnit@0x%x to %s\n", unitCatalogList, units_filename);
		DumpIds(sc2_handle, unitCatalogList, stringNameOffset, units_file);
		fclose(units_file);
	} else {
		printf("  ERROR: Could not open %s for writing.",units_filename);
	}

	printf("\nDone.\n");
	CloseHandle(sc2_handle);
    return 0;
}

void DumpIds(HANDLE sc2_handle, uint32_t catalogRecordList, uint32_t stringNameOffset, FILE* out) {
	uint32_t recordsList = ReadUInt(catalogRecordList + 0x5c, sc2_handle);
	if (recordsList == 0) {
		printf("-- Error dumping table@%x: no list of catalog records found.\n", catalogRecordList);
		return;
	}

	uint32_t numEntries = ReadUInt(catalogRecordList + 0x50, sc2_handle);
	for (uint32_t id = 0; id < numEntries; id++) {
		uint32_t recordPtr = ReadUInt(recordsList + 4 * id, sc2_handle);
		if (recordPtr != 0) {
			uint32_t stringPtr = ReadUInt(ReadUInt(recordPtr + stringNameOffset, sc2_handle) + 0x10, sc2_handle) + 4;
			uint32_t stringLength = ReadUInt(stringPtr, sc2_handle);
			uint32_t string_flags = ReadUInt(stringPtr + 4,sc2_handle);

			// Some strings are actually stored else where in memory
			uint32_t stringDataPtr = stringPtr+8;
			if (string_flags & 4) {
				stringDataPtr = ReadUInt(stringDataPtr,sc2_handle);
			}

			char* name = ReadString(stringDataPtr, stringLength, sc2_handle);
			if (strlen(name) != 0) {
				fprintf(out, "%d,%s\n", id, name);
			}
			free(name);
		}
	}
}

char* ReadString(uint32_t address, uint32_t length, HANDLE sc2_handle) {
	char* result = (char*)malloc(length+1);
	memset(result, 0, length+1);
	ReadProcessMemory(sc2_handle, (LPCVOID)address, result, length, 0);
	return result;
}

uint32_t ReadUInt(uint32_t address, HANDLE sc2_handle) {
  uint32_t result = 0;
  ReadProcessMemory(sc2_handle, (LPCVOID)address, &result, sizeof(uint32_t), 0);
  return result;
}

uint32_t GetModuleBase(DWORD procId, char* modName)
{
  HANDLE snapshot;
  MODULEENTRY32 modInfo;
  snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, procId);
  modInfo.dwSize = sizeof(MODULEENTRY32);

  if (Module32First(snapshot, &modInfo))
  {
    // printf("mod %s\n", modInfo.szModule);
    if (!strcmp(modInfo.szModule, modName))
    {
      CloseHandle(snapshot);
      return (uint32_t)modInfo.modBaseAddr;
    }

    while (Module32Next(snapshot, &modInfo))
    {
      // printf("mod %s\n", modInfo.szModule);
      if (!strcmp(modInfo.szModule, modName))
      {
        CloseHandle(snapshot);
        return (uint32_t)modInfo.modBaseAddr;
      }
    }
  }
  CloseHandle(snapshot);
  return 0;
}

char* getSC2Info(HANDLE sc2_handle, uint32_t &base_address, uint32_t &build) {
	char* sc2_exe_path = (char*)malloc(MAX_PROC_NAME_SIZE);
	if(GetModuleFileNameEx(sc2_handle, 0, sc2_exe_path, MAX_PROC_NAME_SIZE)==0) {
		printf("ERROR %d: Unable to retrieve executable file name", GetLastError());
		return NULL;
	}

	DWORD infoSize = GetFileVersionInfoSize(sc2_exe_path, 0);
	void *infoBuffer = malloc(infoSize);
	VS_FIXEDFILEINFO *sc2VersionInfo;

	GetFileVersionInfo(sc2_exe_path, 0, infoSize, infoBuffer);
	VerQueryValue(infoBuffer, "\\", (LPVOID*)&sc2VersionInfo, 0);
	build = sc2VersionInfo->dwFileVersionLS & 0xffff;
	free(infoBuffer);

	DWORD proc_id = GetProcessId(sc2_handle);
	base_address = GetModuleBase(proc_id, "SC2.exe");
	return sc2_exe_path;
}

HANDLE getSC2Handle() {	
	DWORD bytes_returned = 0;
	DWORD proc_ids[MAX_PROC_LIST_SIZE]; // Should be large enough
	if (EnumProcesses(proc_ids, MAX_PROC_LIST_SIZE, &bytes_returned)!=0) {
		char buf[MAX_PROC_NAME_SIZE];
		DWORD proc_count = bytes_returned/sizeof(DWORD);
		for (DWORD i=0; i < proc_count; i++) {
			DWORD proc_id = proc_ids[i];
			HANDLE handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, proc_id);
			if (handle != NULL) {
				if(GetModuleBaseName(handle, 0, buf, MAX_PROC_NAME_SIZE)!=0 && strcmp(buf, "SC2.exe")==0) {
					return handle;
				} else {
					CloseHandle(handle);
				}
			}
		}
    } else {
		printf("Error %d: Unable to enumerate processes.\n",GetLastError());
    }
	return NULL;
}
