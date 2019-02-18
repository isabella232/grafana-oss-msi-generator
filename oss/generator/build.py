#!/usr/bin/env python
#
# Creates .wxs files to be used to generate multiple MSI targets
#
# by default the script will check for dist and enterprise-dist, and parse the version as needed
# options are provided to give a build version that will download the zip, drop in to dist/enterprise-dist and do the same thing
#
# Expected paths and names 
# dist/grafana-6.0.0-ca0bc2c5pre3.windows-amd64.zip
# enterprise-dist/grafana-enterprise-6.0.0-29b28127pre3.windows-amd64.zip
#
# Optionally (mainly for testing), pass arguments to pull a specific build
#   -b,--build 5.4.3
#   -e,--enterprise add this flag to specify enterprise
#   -p,--premium, add this flag to include premium plugins
#
# When using the build option, the zip file is created in either dist or dist-enterprise according to the -e flag toggle.
#
# https://s3-us-west-2.amazonaws.com/grafana-releases/release/grafana-{}.windows-amd64.zip
#
# https://dl.grafana.com/enterprise/release/grafana-enterprise-{}.windows-amd64.zip 
#
import os
from jinja2 import Template, Environment, FileSystemLoader
import wget
import zipfile
import tempfile
import subprocess
import shutil
import argparse
import glob
import re

from utils import *

#############################
# Constants - DO NOT CHANGE #
#############################
OSS_UPGRADE_VERSION='35c7d2a9-6e23-4645-b975-e8693a1cef10'
OSS_PRODUCT_NAME="Grafana OSS"
ENTERPRISE_UPGRADE_VERSION='d534ec50-476b-4edc-a25e-fe854c949f4f'
ENTERPRISE_PRODUCT_NAME="Grafana Enterprise"


#############################
# paths
#############################
WIX_HOME='/home/xclient/wix'
WINE_CMD='/usr/bin/wine64' # or just wine for 32bit
CANDLE='{} {}/candle.exe'.format(WINE_CMD, WIX_HOME)
LIGHT='{} {}/light.exe'.format(WINE_CMD, WIX_HOME)
HEAT='{} {}/heat.exe'.format(WINE_CMD, WIX_HOME)
NSSM_VERSION='2.24'
#############################
#
#############################
grafana_oss = {
  'feature_component_group_refs': [
    'GrafanaX64',
    'GrafanaServiceX64',
    'GrafanaFirewallExceptionsGroup'
  ],
  'directory_refs': [
    'GrafanaX64Dir'
  ],
  'components': [
    'grafana.wxs',
    'grafana-service.wxs',
    'grafana-firewall.wxs'
  ]
}

def build_oss(zipFile, PRODUCT_VERSION, config, features):
    # keep reference to source directory, will need to switch back and forth during the process
    src_dir = os.getcwd()
    #target_dir = tempfile.TemporaryDirectory()
    if not os.path.isdir('/tmp/a'):
        os.mkdir('/tmp/a')
    target_dir_name = '/tmp/a'
    extract_zip(zipFile, target_dir_name)
    print("Heat Harvesting")
    cgname = 'GrafanaX64'
    cgdir = 'GrafanaX64Dir'
    if not os.path.isdir('/tmp/scratch'):
        os.mkdir('/tmp/scratch')
    os.chdir('/tmp/scratch')
    outfile = 'grafana-oss.wxs'
    # important flags
    # -srd - prevents the parent directory name from being included in the harvest
    # -cg - component group to be referenced in main wxs file
    # -fr - directory ref to be used in main wxs file
    try:
        cmd = '''
          {} dir {} \
          -platform x64 \
          -sw5150 \
          -srd \
          -cg {} \
          -gg \
          -sfrag \
          -dr {} \
          -template fragment \
          -out {}'''.strip().format(HEAT, target_dir_name, cgname, cgdir, outfile)
        print(cmd)
        os.system(cmd)
    except Exception as ex:
        print(ex)

    #os.system('ls -al')
    shutil.copy2(outfile, target_dir_name)
    nssm_file = get_nssm('/tmp/cache', NSSM_VERSION)
    if not os.path.isdir(target_dir_name + '/nssm'):
        os.mkdir(target_dir_name + '/nssm')
    extract_zip(nssm_file, target_dir_name + '/nssm')
    #os.system("ls -l " + target_dir.name + '/nssm-2.24/*')
    #exit(0)
    #os.system('ls -al {}'.format(target_dir.name))
    print("HARVEST COMPLETE")
    os.chdir(src_dir)
    generate_firewall_wxs(env, PRODUCT_VERSION, '/tmp/scratch/grafana-firewall.wxs', target_dir_name)
    generate_service_wxs(env, PRODUCT_VERSION, '/tmp/scratch/grafana-service.wxs', target_dir_name, NSSM_VERSION)
    generate_product_wxs(env, config, features, '/tmp/scratch/product.wxs', target_dir_name)
    #os.system("cat /tmp/scratch/product.wxs")
    print("GENERATE COMPLETE")
    copy_static_files(target_dir_name)
    print("COPY STATIC COMPLETE")
    #
    # ${CANDLE} -ext WixFirewallExtension -ext WixUtilExtension -v -arch x64 grafana-service.wxs
    #if [ ! -e grafana-service.wixobj ]; then
    #echo "Candle failed"
    #exit -1
    #fi
    # for CANDLE, it needs to run in the working dir
    os.chdir('/tmp/scratch')
    try:
        filename = 'grafana-service.wxs'
        cmd = '{} -ext WixFirewallExtension -ext WixUtilExtension -v -arch x64 {}'.format(
          CANDLE,
          filename)
        print(cmd)
        os.system(cmd)
        shutil.copy2('grafana-service.wixobj', target_dir_name)
        #
        filename = 'grafana-firewall.wxs'
        cmd = '{} -ext WixFirewallExtension -ext WixUtilExtension -v -arch x64 {}'.format(
          CANDLE,
          filename)
        print(cmd)
        os.system(cmd)
        shutil.copy2('grafana-firewall.wixobj', target_dir_name)
        #
        filename = 'grafana-oss.wxs'
        cmd = '{} -ext WixFirewallExtension -ext WixUtilExtension -v -arch x64 {}'.format(
          CANDLE,
          filename)
        print(cmd)
        os.system(cmd)
        shutil.copy2('grafana-oss.wixobj', target_dir_name)
        #
        filename = 'product.wxs'
        cmd = '{} -ext WixFirewallExtension -ext WixUtilExtension -v -arch x64 {}'.format(
          CANDLE,
          filename)
        print(cmd)
        os.system(cmd)
        shutil.copy2('product.wixobj', target_dir_name)
    except Exception as ex:
        print(ex)
    #os.system('sleep 600')
    print("CANDLE COMPLETE")
    print("LIGHT COMPLETE")
    #os.system('ls -al {}'.format(target_dir.name))
    ######
    # Relocate files
    ######
    #mv ${EXTRACT_TMP}/grafana-oss/* ${WIX_OUTPUT}
    #mv ${EXTRACT_TMP}/nssm/* ${WIX_OUTPUT}
    ############################
    # LIGHT - Assemble the MSI
    ############################
    os.chdir(target_dir_name)
    os.system('ls -al grafana-5.4.3')
    os.system('cp -pr nssm/nssm-2.24 .')
    #os.system('ls -alR nssm-2.24')

    try:
        cmd = '''
          {} \
          -cultures:en-US \
          -ext WixUIExtension.dll -ext WixFirewallExtension -ext WixUtilExtension \
          -v -sval -spdb \
          grafana-service.wixobj \
          grafana-firewall.wixobj \
          grafana-oss.wixobj \
          product.wixobj \
          -out grafana.msi'''.strip().format(LIGHT)
        print(cmd)
        os.system(cmd)
    except Exception as ex:
        print(ex)
    # copy to scratch with version included
    msi_filename = '/tmp/scratch/grafana-{}-amd64.msi'.format(PRODUCT_VERSION)
    shutil.copy2('grafana.msi', msi_filename)
    os.system('ls -al /tmp/scratch')
    # finally cleanup
    #extract_dir.cleanup()


def main(file_loader, env, grafanaVersion, zipFile):
    UPGRADE_VERSION=OSS_UPGRADE_VERSION
    GRAFANA_VERSION=grafanaVersion
    PRODUCT_NAME=OSS_PRODUCT_NAME
    PRODUCT_VERSION=GRAFANA_VERSION
    # MSI version cannot have anything other than a x.x.x.x format, numbers only
    PRODUCT_MSI_VERSION=GRAFANA_VERSION.split('-')[0]
    #file_content = generate_firewall_wxs(env, PRODUCT_VERSION)
    #print(file_content)
    #file_content = generate_service_wxs(env, PRODUCT_VERSION, NSSM_VERSION)
    #print(file_content)

    config = {
      'grafana_version': PRODUCT_VERSION,
      'upgrade_code': UPGRADE_VERSION,
      'product_name': PRODUCT_NAME,
      'manufacturer': 'Grafana Labs'
    }
    features = [
      {
        'name': 'GrafanaOSS',
        'title': PRODUCT_NAME,
        'component_groups': [
          {
          'ref_id': 'GrafanaX64',
          'directory': 'GrafanaX64Dir'
          }
        ]
      },
      {
        'name': 'GrafanaService',
        'title': 'Run Grafana as a Service',
        'component_groups': [
          {
          'ref_id': 'GrafanaServiceX64',
          'directory': 'GrafanaServiceX64Dir'
          }
        ]
      }
    ]
    build_oss(zipFile, PRODUCT_VERSION, config, features)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Grafana MSI Generator',
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=90, width=110),add_help=True)
    parser.add_argument('-p', '--premium', help='Flag to include premium plugins', dest='premium', action='store_true')
    parser.add_argument('-e', '--enterprise', help='Flag to use enterprise build', dest='enterprise', action='store_true')
    parser.set_defaults(enterprise=False, premium=False)

    parser.add_argument('-b', '--build', help='build to download')
    args = parser.parse_args()
    file_loader = FileSystemLoader('templates')
    env = Environment(loader=file_loader)
    grafanaVersion = None
    grafanaHash = None
    isEnterprise = False
    if not os.path.isdir('/tmp/dist'):
        os.mkdir('/tmp/dist')
    # if a build version is specified, pull it
    if (args.build):
        grafanaVersion = args.build
    else:
        grafanaVersion, grafanaHash, isEnterprise = detect_version('/tmp/dist')
        
    # check for enterprise flag
    if (args.enterprise):
        grafanaVersion = 'enterprise-{}'.format(args.build)
    #
    print('Detected Version: {}'.format(grafanaVersion))
    if (grafanaHash):
        print('Detected Hash: {}'.format(grafanaHash))
    print('Enterprise: {}'.format(isEnterprise))
    if isEnterprise:
        zipFile = '/tmp/dist/grafana-enterprise-{}.windows-amd64.zip'.format(grafanaVersion)
    else:
        zipFile = '/tmp/dist/grafana-{}.windows-amd64.zip'.format(grafanaVersion)
    print('ZipFile: {}'.format(zipFile))
    # check if file downloaded

    if not os.path.isfile(zipFile):
        zipFile = get_zip(grafanaVersion, zipFile)
    main(file_loader, env, grafanaVersion, zipFile)

