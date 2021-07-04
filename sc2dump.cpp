/* Dump type ids for Units and Abils for SC2.
 *
 * Authors: Robert Nix (@mischanix), Graylin Kim (@GraylinKim)
 *
 * to compile with mingw-w64-x86_64-clang:
 *   clang -Wextra -Wall -Werror -O3 sc2dump.cpp -static -lversion -lpsapi
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
 */

#include <Windows.h>
#include <psapi.h>
#include <TlHelp32.h>

#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define MODULE_NAME "SC2_x64.exe"
typedef uint64_t rptr_t;
#define PTR(x) (const void *)(x)

HANDLE sc2_handle;

char* ReadString(rptr_t address, uint32_t length) {
	char* result = (char*)malloc(length+1);
	memset(result, 0, length+1);
	ReadProcessMemory(sc2_handle, PTR(address), result, length, 0);
	return result;
}

uint32_t ReadUInt(rptr_t address) {
	uint32_t result = 0;
	ReadProcessMemory(sc2_handle, PTR(address), &result, sizeof(uint32_t), 0);
	return result;
}

rptr_t ReadPtr(rptr_t address) {
	rptr_t result = 0;
	ReadProcessMemory(sc2_handle, PTR(address), &result, sizeof(rptr_t), 0);
	return result;
}

void DumpIds(rptr_t catalogRecordList, rptr_t stringNameOffset, FILE* out) {
	rptr_t recordsList = ReadPtr(catalogRecordList + 0x48);
	if (recordsList == 0) {
		printf("-- Error dumping table@%p: no list of catalog records found.\n", PTR(catalogRecordList));
		return;
	}

	uint32_t numEntries = ReadUInt(catalogRecordList + 0x38);
	printf("%u %p\n", numEntries, PTR(recordsList));
	for (uint32_t id = 0; id < numEntries; id++) {
		rptr_t recordPtr = ReadPtr(recordsList + sizeof(rptr_t) * id);
		if (recordPtr != 0) {
			rptr_t stringPtr = ReadPtr(ReadPtr(recordPtr + stringNameOffset) + 0x20) + 0x18;
			uint32_t stringLength = ReadUInt(stringPtr) >> 2;
			uint32_t stringFlags = ReadUInt(stringPtr + 4);

			// Strings are either inline or a pointer depending on length:
			rptr_t stringDataPtr = stringPtr + 8;
			if (stringFlags & 2) {
				stringDataPtr = ReadPtr(stringDataPtr);
			}

			char* name = ReadString(stringDataPtr, stringLength);
			if (strlen(name) != 0) {
				fprintf(out, "%d,%s\n", id, name);
			}
			free(name);
		}
	}
}

rptr_t GetModuleBase(DWORD procId, const char* modName)
{
	HANDLE snapshot;
	MODULEENTRY32 modInfo;
	snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPMODULE, procId);
	modInfo.dwSize = sizeof(MODULEENTRY32);

	if (Module32First(snapshot, &modInfo))
	{
		if (!strcmp(modInfo.szModule, modName))
		{
			CloseHandle(snapshot);
			return (rptr_t)(uintptr_t)modInfo.modBaseAddr;
		}

		while (Module32Next(snapshot, &modInfo))
		{
			if (!strcmp(modInfo.szModule, modName))
			{
				CloseHandle(snapshot);
				return (rptr_t)(uintptr_t)modInfo.modBaseAddr;
			}
		}
	}
	CloseHandle(snapshot);
	return 0;
}

char* getSC2Info(rptr_t &base_address, uint32_t &build) {
	char* sc2_exe_path = (char*)malloc(512);
	if(GetModuleFileNameEx(sc2_handle, 0, sc2_exe_path, 512)==0) {
		printf("ERROR %lu: Unable to retrieve executable file name", GetLastError());
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
	base_address = GetModuleBase(proc_id, MODULE_NAME);
	return sc2_exe_path;
}

HANDLE getSC2Handle() {
	DWORD bytes_returned = 0;
	DWORD proc_ids[2048]; // Should be large enough
	if (EnumProcesses(proc_ids, 2048, &bytes_returned)!=0) {
		char buf[512];
		DWORD proc_count = bytes_returned/sizeof(DWORD);
		for (DWORD i=0; i < proc_count; i++) {
			DWORD proc_id = proc_ids[i];
			HANDLE handle = OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, 0, proc_id);
			if (handle != NULL) {
				if(GetModuleBaseName(handle, 0, buf, 512)!=0 && strcmp(buf, MODULE_NAME)==0) {
					return handle;
				} else {
					CloseHandle(handle);
				}
			}
		}
	} else {
		printf("Error %lu: Unable to enumerate processes.\n", GetLastError());
	}
	return NULL;
}

int main(int argc, char *argv[]) {
	if (argc < 3) {
		printf("Both unit and ability output files are required (in that order).\n");
		ExitProcess(1);
	}

	char *units_filename = argv[1];
	char *abils_filename = argv[2];

	printf("Searching for a live SC2 process.\n");
	sc2_handle = getSC2Handle();
	if (sc2_handle == NULL) {
		printf("Error: " MODULE_NAME " not found\n");
		ExitProcess(1);
	}

	uint32_t build;
	rptr_t base_address;
	char* sc2_exe_path = getSC2Info(base_address, build);
	if (sc2_exe_path == NULL) {
		printf("Error: Unable to acquire base address and build information.\n");
		ExitProcess(1);
	} else {
		printf("\nFound " MODULE_NAME "\n");
		printf("  Path: %s\n", sc2_exe_path);
		printf("  Base Address: %p\n", PTR(base_address));
		printf("  Build: %d\n", build);
	}

	rptr_t gameCatalog = 0;
	uint32_t cUnitIndex = 0;
	uint32_t stringNameOffset = 0;
	switch(build) {
	case 37164: // LotV beta 2.5.5.37164
		gameCatalog = 0x3E7DC58u;
		cUnitIndex = 0x280u;
		stringNameOffset = 0x70u;
		break;
	default:
		printf("Error: Missing offset values for build %d\n", build);
		ExitProcess(1);
	}

	rptr_t gameCatalogTable = ReadPtr(base_address + gameCatalog);
	printf("\nDumping Catalog@0x%p\n", PTR(gameCatalogTable));

	FILE* abils_file;
	if (fopen_s(&abils_file, abils_filename, "w") == 0) {
		rptr_t abilCatalogList = ReadPtr(gameCatalogTable + 0x8);
		printf("  Dumping CAbil@0x%p to %s\n", PTR(abilCatalogList), abils_filename);
		DumpIds(abilCatalogList, stringNameOffset, abils_file);
		fclose(abils_file);
	} else {
		printf("  ERROR: Could not open %s for writing\n", abils_filename);
	}

	FILE* units_file;
	if (fopen_s(&units_file, units_filename, "w") == 0) {
		rptr_t unitCatalogList = ReadPtr(gameCatalogTable + cUnitIndex);
		printf("  Dumping CUnit@0x%p to %s\n", PTR(unitCatalogList), units_filename);
		DumpIds(unitCatalogList, stringNameOffset, units_file);
		fclose(units_file);
	} else {
		printf("  ERROR: Could not open %s for writing.\n", units_filename);
	}

	printf("\nDone.\n");
	CloseHandle(sc2_handle);
	return 0;
}
