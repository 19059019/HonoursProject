# Command Line Interface

 This directory contains the command line interface application that allows a user to communicate with the webapp from a bash terminal with python installed. The **StandaloneFunctions** contains all of the functionality that makes up the _assignments.py_ application.

 ## Usage

 To be able to use the assignments function, make it executable and move it into **/usr/local/bin** as follows:
 ```
 sudo mv assignments /usr/local/bin
 sudo chmod +x /usr/local/bin/assignments
 ```

 Once the application is installed, the usage is as follows:
 ```
 Student:
 Get Assignment: assignment <suid> <assignment code>
 Submit Assignment: assignment <suid> submit <zip file path> <assignment code>
 Start Assignment:assignment <suid> start <assignment code>
 
 Lecturer:
 Get Files: assignment <suid> get
 Create Assignment: assignment <suid> create <sub.json path> [env.json path]
 Get Submissions: assignment <suid> download <assignment code>
 Add Students from File: assignments add  <suid> <module> <student file path>
 ```
