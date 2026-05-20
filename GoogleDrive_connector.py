
import os
import requests


def update_index_file(local_index_file_path: str):
    index_file_id = "1Cr_4tQTBjm9yiAk_yO8MI92HMdb74oTW"
    retrieve_file_from_google_drive(
        file_path=local_index_file_path,
        file_id=index_file_id
    )


def retrieve_file_from_google_drive(file_path: str, file_id: str):
    _, file_extension = os.path.splitext(file_path)
    query_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"
    match file_extension:
        case ".json":
            response = requests.get(query_url, timeout=5)
            response.raise_for_status()
            with open(file_path, mode="wb") as file:
                file.write(response.content)
        case ".gz":
            with open(file_path, 'wb') as file, requests.get(query_url, stream=True) as response:
                for chunk in response.raw.stream(1024, decode_content=False):
                    if chunk:
                        file.write(chunk)
                # for line in response.iter_lines():
                #     file.write(line + '\n'.encode())
        case ".txt":
            response = requests.get(query_url, timeout=5)
            response.raise_for_status()
            with open(file_path, "w+") as file:
                file.write(response.text)
        case _:
            raise Exception(f"Unexpected file extension: {file_extension}")


def import_files_index(index_path: str) -> dict:
    with open(index_path, 'r') as file:
        lines = file.read().splitlines()
    index = dict()
    for line in lines:
        if not line:
            continue
        name, identifier = line.split("|")
        index[name.strip()] = identifier.strip()
    return index


def get_list_of_local_files(local_files_path: str):
    local_files = [file for file in os.listdir(local_files_path) if os.path.isfile(os.path.join(local_files_path, file)) and not file == ".gitignore"]
    return local_files


def detect_changes(local_files: list[str], index: dict, extension: None | str = None):
    new_files = set(index.keys())
    current_files = set(local_files)
    if extension:
        new_files = set([file for file in new_files if os.path.splitext(file)[1] == extension])
        current_files = set([file for file in current_files if os.path.splitext(file)[1] == extension])
    files_to_add = new_files - current_files
    files_to_delete = current_files - new_files
    files_to_add = {key: value for key, value in index.items() if key in files_to_add}
    return files_to_add, files_to_delete


def patch_changes(local_files_path: str, files_to_add: dict[str: str], files_to_delete: set[str]):
    for file in files_to_delete:
        os.remove(os.path.join(local_files_path, file))

    for file_name, file_id in files_to_add.items():
        retrieve_file_from_google_drive(
            file_path=os.path.join(local_files_path, file_name),
            file_id=file_id
        )


def synchronize_info(local_files_path: str, index: dict):
    local_files = get_list_of_local_files(local_files_path)
    files_to_add, _ = detect_changes(local_files=local_files, index=index, extension=".json")
    patch_changes(local_files_path, files_to_add, set())


def synchronize_data(local_files_path: str, index: dict):
    local_files = get_list_of_local_files(local_files_path)
    files_to_add, _ = detect_changes(local_files=local_files, index=index, extension=".gz")
    patch_changes(local_files_path, files_to_add, set())


def synchronize(local_files_path: str):
    index_file_path = os.path.join(local_files_path, "index.txt")
    update_index_file(index_file_path)
    new_index_file = import_files_index(index_file_path)
    local_files = get_list_of_local_files(local_files_path)
    files_to_add, files_to_delete = detect_changes(local_files, new_index_file)
    patch_changes(local_files_path, files_to_add, files_to_delete)


if __name__ == "__main__":
    files_directory = "test"
    synchronize(local_files_path=files_directory)
