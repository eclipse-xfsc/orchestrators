#!/bin/bash

# This is the script that is used to package the examples for GXFS Orchestration.
# Examples are packaged (zipped) into destination folder along with their inputs (if those exists)
# This script is used within the CI/CD, but you can also run it manually with: ./package.sh <your-destination-folder>

# get destination folder
destination_folder="$1"

# check destination folder, create it if it does not exist
[[ -z "$destination_folder" ]] && echo "Missing path to destination folder (the first argument)." && exit 1
[[ ! -d "$destination_folder" ]] && mkdir -p "$destination_folder"

# get absolute path to destination folder
destination_folder=$(realpath "$destination_folder")

# function for packaging (zipping) one example
package_example() {
    # set base path and check if set
    example_base_path="$1"
    [[ -z "$example_base_path" ]] && echo "Missing path to example (the first argument)." && exit 1
    [[ ! -d "$example_base_path" ]] && echo "Path to example should be a directory." && exit 1
    # get absolute path to base folder
    example_base_path_abs=$(realpath "$example_base_path")

    # set other paths and check them
    example_iac_path="${example_base_path_abs}/iac"
    example_inputs_path="${example_base_path_abs}/inputs"
    [[ ! -d "$example_iac_path" ]] && echo "Example folder should contain a directory called 'iac'." && exit 1

    # set destination zip file
    destination_zip_file="${destination_folder}/${example_base_path//\//_}_iac.zip"

    # zip example IaC
    cd "$example_iac_path" || true
    printf "\nZipping %s to %s ...\n" "$example_iac_path" "$destination_zip_file"
    zip -qq -r "$destination_zip_file" .
    cd - >/dev/null || true

    # copy inputs if there are any
    if [ -d "$example_inputs_path" ]; then
        # shellcheck disable=SC2012
        inputs_count=$(ls "$example_inputs_path" | wc -l)
        [[ "$inputs_count" -ne 1 ]] && echo "There should be only one input file." && exit 1

        input_file=$(ls "$example_inputs_path")
        printf "Copying %s to %s ...\n" "${example_inputs_path}/${input_file}" "${destination_folder}/${example_base_path//\//_}_${input_file}"
        cp -r "${example_inputs_path}/${input_file}" "${destination_folder}/${example_base_path//\//_}_${input_file}"
    fi

    printf "  Done!\n"
    return 0
}

# start packaging
printf "Packaging examples ...\n"

# package examples from tosca/ folder
package_example "tosca/aws-thumbnail-generator"
package_example "tosca/hello-world"
package_example "tosca/nginx-openstack"

# package examples from terraform/ folder
package_example "terraform/hello-world"
package_example "terraform/nginx-ionos"
package_example "terraform/nginx-openstack"
