#!/usr/bin/expect -f
# Copyright (C) 2013-2014, KulCloud Inc. Ltd.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See
#    the
#    License for the specific language governing permissions and limitations
#    under the License.
set timeout -1;
log_user 0
set device [lindex $argv 0];
set cmd [lindex $argv 1];
send_user "\nDevice: $device. Try to send cmd $cmd\n"
spawn ssh admin@10.1.160.222
expect "password:"
send "kulpass@123\r"
expect ">"
send "configure\r"
log_user 1
expect "#"
send "$cmd\r"

expect "*More*" 
while {1} {
    send "\r\n"
    expect {
        "*More*" {
            continue
        }
        "#" {
            send "q\r"
            exit
            break
        }
    }
}

send "q\r"
send "q\r"
send "q\r"

expect eof