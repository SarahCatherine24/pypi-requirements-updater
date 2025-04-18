import requests
from bs4 import BeautifulSoup
import re

HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_latest_version_and_check_compatibility(package_name):
    package_name = package_name.replace('_', '-')
    url = f"https://pypi.org/project/{package_name}/"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        print(f"Failed to fetch data for {package_name}")
        return None, False
    '''
    if "Not Found" in response.text or "does not exist" in response.text:
        print(f"Package {package_name} not found on PyPI")
        return None, False

    '''
    
    soup = BeautifulSoup(response.text, 'html.parser')
    version_tag = soup.find('h1', class_='package-header__name')
    latest_version = None
    if version_tag:
        version_match = re.search(r'\b(\d+\.\d+\.\d+)\b', version_tag.text)
        if version_match:
            latest_version = version_match.group(1)
    
    classifiers = soup.find_all('ul', class_='sidebar-section__classifiers')
    is_python_311_compatible = any(
        "Python :: 3.11" in classifier.text or "Python :: 3" in classifier.text 
        for classifier in classifiers)
    
    return latest_version, is_python_311_compatible

def update_requirements(input_file, output_file):
    with open(input_file, 'r') as f:
        packages = f.readlines()
    
    updated_packages = []
    inline_updates = []

    for package in packages:
        package = package.strip()
        
        if package.startswith("--extra-index-url") or "@" in package or package.startswith("#"):
            updated_packages.append(package + "\n")
            inline_updates.append(package + "\n")
            continue
        
        package_name = package.split("==")[0]
        latest_version, is_compatible = get_latest_version_and_check_compatibility(package_name)
        
        if latest_version:
            if is_compatible:
                updated_packages.append(f"{package_name}=={latest_version}\n")
                inline_updates.append(f"{package}  # Updated to {latest_version}\n")
            else:
                print(f"Skipping {package_name}: Not compatible with Python 3.11")
                updated_packages.append(package + "\n")
                inline_updates.append(package + "\n")
        else:
            updated_packages.append(package + "\n")
            inline_updates.append(package + "\n")  # Keep the original package if not found

    # Approach 1: Writing to a separate updated_requirements.txt file
    with open(output_file, 'w') as f:
        f.writelines(updated_packages)
    print(f"Updated requirements saved to {output_file}")

    # Approach 2: Updating the same requirements.txt file inline
    with open(input_file, 'w') as f:
        f.writelines(inline_updates)
    print(f"Original {input_file} updated with inline comments for version changes.")

    # Logging unchanged packages
    with open(input_file, 'r') as f1, open(output_file, 'r') as f2:
        original_lines = f1.readlines()
        updated_lines = f2.readlines()

    unchanged_packages = [
        orig.strip() for orig, updated in zip(original_lines, updated_lines) if orig.strip() == updated.strip()
    ]

    if unchanged_packages:
        print("\nUnchanged Packages:")
        for pkg in unchanged_packages:
            if pkg.startswith("--extra-index-url") or "@" in pkg or pkg.startswith("#"):
                continue
            print(pkg)


def main():
    update_requirements('requirements.txt', 'updated_requirements.txt')

if __name__ == "__main__":
    main()
