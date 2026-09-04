package architecture_test

import (
	"encoding/json"
	"os/exec"
	"strings"
	"testing"
)

func TestDomainPackagesDoNotImportAdaptersOrGeneratedTransport(t *testing.T) {
	t.Parallel()

	command := exec.Command("go", "list", "-json", "./internal/...")
	command.Dir = "../.."
	output, err := command.Output()
	if err != nil {
		t.Fatalf("go list: %v", err)
	}

	decoder := json.NewDecoder(strings.NewReader(string(output)))
	for decoder.More() {
		var packageInfo struct {
			ImportPath   string
			Imports      []string
			TestImports  []string
			XTestImports []string
		}
		if err := decoder.Decode(&packageInfo); err != nil {
			t.Fatalf("decode go list output: %v", err)
		}
		if !isDomainPackage(packageInfo.ImportPath) {
			continue
		}
		for _, imported := range append(append(packageInfo.Imports, packageInfo.TestImports...), packageInfo.XTestImports...) {
			if strings.Contains(imported, "/internal/platform/") ||
				strings.Contains(imported, "/internal/gen/") ||
				strings.Contains(imported, "/internal/app") {
				t.Errorf("domain package %s imports forbidden boundary %s", packageInfo.ImportPath, imported)
			}
		}
	}
}

func isDomainPackage(importPath string) bool {
	const internalMarker = "/backend/internal/"
	_, suffix, found := strings.Cut(importPath, internalMarker)
	if !found {
		return false
	}
	topLevel := strings.SplitN(suffix, "/", 2)[0]
	switch topLevel {
	case "app", "architecture", "gen", "platform":
		return false
	default:
		return true
	}
}
