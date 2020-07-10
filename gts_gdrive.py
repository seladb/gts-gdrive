import os
import argparse
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import yaml
import github_traffic_stats

class MissingConfigExcpetion(Exception):
    pass

class MissingGithubConfigException(Exception):
    pass

def __load_config():
    if not os.path.exists('settings.yaml'):
        raise MissingConfigExcpetion

    with open('settings.yaml', 'r') as settings_file:
        return yaml.load(settings_file, Loader=yaml.FullLoader)

def __load_github_config():
    settings = __load_config()
    if not 'github' in settings:
        raise MissingGithubConfigException

    return settings['github']

def __load_config_and_auth():
    github_config = __load_github_config()

    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()

    gdrive = GoogleDrive(gauth)

    return gdrive, github_config

def __download_db(gdrive, github_config):
    db_name = '{repo}_views.db'.format(repo=github_config['repo'])
    file_list1 = gdrive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

    for file1 in file_list1:
        if file1['title'] == db_name:
            file1.GetContentFile(db_name, mimetype=file1['mimeType'])
            break

def __upload_db(gdrive, github_config):
    db_name = '{repo}_views.db'.format(repo=github_config['repo'])
    file_list1 = gdrive.ListFile({'q': "'root' in parents and trashed=false"}).GetList()

    for file1 in file_list1:
        if file1['title'] == db_name:
            file1.SetContentFile(db_name)
            file1.Upload()
            break

def configure(gdrive_client_id, gdrive_client_secret, username, repo, github_access_token):
    config = {
        'client_config_backend': 'settings',
        'client_config': {
            'client_id': gdrive_client_id,
            'client_secret': gdrive_client_secret
        },
        'save_credentials': True,
        'save_credentials_backend': 'file', 
        'save_credentials_file': 'creds.json', 
        'oauth_scope': ['https://www.googleapis.com/auth/drive'],
        'github': {
            'username': username,
            'repo': repo,
            'access_token': github_access_token
        }
    }
    with open('settings.yaml', 'w') as settings_file:
        yaml.dump(config, settings_file)

    return __load_config_and_auth()

def github_config(username, repo):
    config = __load_config()
    config['github']['username'] = username
    config['github']['repo'] = repo
    with open('settings.yaml', 'w') as settings_file:
        yaml.dump(config, settings_file)

def config_walkthrough():
    print("Welcome!\n\nThis guide will walk you through gts-gdrive configuration.")
    print("During the setup you will be asked to provide Github repo details to fetch data from,")
    print("as well as Google Drive authentication details where the stats data will be stored")
    print("\nLet's start with Google Drive authentication.")
    print("If you don't have 'client_secrets.json' already please follow this guide to understand how to get it:")
    print("https://help.talend.com/reader/E3i03eb7IpvsigwC58fxQg/uEUUsDd_MSx64yoJgSa1xg")
    print("\n")
    gdrive_client_id = input("Please provide Google Drive Client ID: ")
    gdrive_client_secret = input("Please provide Google Drive Client Secret: ")

    print("\nNow let's move to Github details.")
    print("You'll need to provide username and repo details (e.g seladb/pcapplusplus)")
    print("and also Github access token which is required to fetch Github traffic data")
    print("If you don't have Github access token, use this link to create one:")
    print("https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fsettings%2Ftokens")
    print("\n")
    github_repo = input("Please provide Github repo to collect stats from: ")
    github_username = input("Please provide Github username of this repo: ")
    github_access_token = input("Please provide Github access token: ")

    configure(gdrive_client_id=gdrive_client_id, gdrive_client_secret=gdrive_client_secret, 
        username=github_username, repo=github_repo, github_access_token=github_access_token)

    print("\nTwo files were create: 'settings.yaml' and 'creds.json'. Please don't delete or modify them.")
    print("Also, be careful who you share them with as they contains your sensitive Google Drive and Github")
    print("authentication information.")

def config_repo_walkthorugh():
    github_repo = input("Please provide Github repo to collect stats from: ")
    github_username = input("Please provide Github username of this repo: ")
    github_config(username=github_username, repo=github_repo)

def view(gdrive, github_config):
    __download_db(gdrive=gdrive, github_config=github_config)
    github_traffic_stats.view(repo=github_config['repo'])

def collect(gdrive, github_config):
    __download_db(gdrive=gdrive, github_config=github_config)
    github_traffic_stats.collect(user=github_config['username'], repo=github_config['repo'], token=github_config['access_token'], org=None)
    __upload_db(gdrive=gdrive, github_config=github_config)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['config', 'config-repo', 'collect', 'view'])
    args = parser.parse_args()

    if args.action == 'config':
        config_walkthrough()
        exit(0)

    try:
        gdrive, github_config = __load_config_and_auth()
    except MissingConfigExcpetion:
        config_walkthrough()
    except MissingGithubConfigException:
        config_walkthrough()

    if args.action == 'config-repo':
        config_repo_walkthorugh()
    elif args.action == 'view':
         view(gdrive=gdrive, github_config=github_config)
    elif args.action == 'collect':
         collect(gdrive=gdrive, github_config=github_config)

if __name__ == "__main__":
    main()
