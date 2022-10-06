#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys

sshrc_file = "./specfile.sshrc"


def parse_line_fields(line_fields, std_keywords):
    line_obj = {}
    std_keywords = [
        "machine",
        "profile",
        "nick",
        "login",
        "password",
        "keyfile",
        "port",
    ]
    for i in range(0, len(line_fields), 2):
        field_name = line_fields[i]
        if field_name in std_keywords:
            line_obj[field_name] = line_fields[i + 1]
        elif field_name == "args":
            line_obj[field_name] = " ".join(line_fields[i + 1 :])
            break
        else:
            sys.stderr.write(
                f"Warning: unrecognized keyword `{field_name}` encountered in {sshrc_file}\n"
            )
    return line_obj


def parse_machine_line(machine_line_fields):
    return parse_line_fields(
        machine_line_fields,
        [
            "machine",
            "profile",
            "nick",
            "login",
            "password",
            "keyfile",
            "port",
        ],
    )


def parse_profile_line(line_fields):
    return parse_line_fields(
        machine_line_fields, ["profile", "login", "password", "keyfile", "port"]
    )


def construct_ssh_command(machine_obj):
    machine_keys = machine_obj.keys()
    if "password" in machine_keys:
        # TODO link password
        os.environ["SSHPASS"] = machine_obj["password"]
        binary = "sshpass -e ssh"
    else:
        binary = "ssh"

    if "login" in machine_keys:
        target = f"{machine_obj['login']}@{machine_obj['machine']}"
    else:
        target = machine_obj["machine"]

    args = ""
    if "keyfile" in machine_keys:
        args += f"-i {machine_obj['keyfile']}"
    if "port" in machine_keys:
        args += f"-i {machine_obj['port']}"
    if "args" in machine_keys:
        args += f"{machine_obj['args']}"

    if binary == "sshpass":
        cmd = f"{binary} {target} {args}"
    else:
        cmd = f"{binary} {args} {target}"

    return cmd.split()


with open(sshrc_file, "r") as infile:
    sshrc_lines = infile.readlines()

# Parse file lines
sshrc = {"machines": [], "profiles": []}
for line in sshrc_lines:
    splitline = line.split()
    if len(splitline) > 0:
        if splitline[0] == "machine":
            machine_obj = parse_machine_line(splitline)
            sshrc["machines"].append(machine_obj)
        elif splitline[0] == "profile":
            profile_obj = parse_machine_line(splitline)
            sshrc["profiles"].append(profile_obj)

# Install keys from profile into machine entry
for machine in sshrc["machines"]:
    if "profile" in machine.keys():
        found_profile = False
        for profile in sshrc["profiles"]:
            if machine["profile"] == profile["profile"]:
                for key in profile.keys():
                    if key not in machine.keys():
                        machine[key] = profile[key]
                found_profile = True
                break
        if not found_profile:
            sys.stderr.write(
                f'Warning: profile `{machine["profile"]}` specified for {machine["machine"]} not found!\n'
            )

# Parse user arguments
parser = argparse.ArgumentParser(
    description="Streamlines SSH access to a commonly-used servers"
)
parser.add_argument(
    "target",
    metavar="<HOSTNAME OR NICK>",
    help="hostname, IP address or nickname to access via SSH",
)
parser.add_argument(
    "-p", "--profile", help="force usage of a specific 'profile' from the ~/.sshrc file"
)
args = parser.parse_args()

# User has specified a profile to use with the host
if args.profile:
    found_profile = False
    for profile in sshrc["profiles"]:
        if args.profile == profile["profile"]:
            machine_obj = {"machine": args.target}
            for key in profile.keys():
                machine_obj[key] = profile[key]
            found_profile = True
    if not found_profile:
        sys.stderr.write(f"Warning: specified profile `{args.profile}` not found!\n")
    else:
        cmd = construct_ssh_command(machine_obj)
        subprocess.run(cmd)
# Search our parsed file object for information on host
else:
    for machine in sshrc["machines"]:
        if args.target == machine["machine"] or (
            "nick" in machine.keys() and args.target == machine["nick"]
        ):
            cmd = construct_ssh_command(machine)
            subprocess.run(cmd)
