#!/bin/bash
# This script prompts the user for a directory, finds .whl files,
# and lists them in a text file with the specified formatting,
# containing only the file name, without the full path.

# The output file name
OUTPUT_FILE="wheels_list.txt"
DIR="wheels"

# Check if the directory exists and is valid
if [ ! -d "$DIR" ]; then
    echo "Error: The directory '$DIR' does not exist or is not a valid directory."
    exit 1
fi

# Start searching for files and creating the output file
echo "Searching for .whl files in '$DIR' and saving to '$OUTPUT_FILE'..."

# Use the find command to search for files and format the output.
# The -printf '"%f",\n' option prints only the file name (%f).
find "$DIR" -type f -name "*.whl" -printf '\047%f\047,\n' > "$OUTPUT_FILE"

echo "Done! The list of .whl files has been saved to '$OUTPUT_FILE'."