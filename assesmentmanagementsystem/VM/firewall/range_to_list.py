from ipaddress import ip_address
import sys

def ips(start_ip, end_ip):
   start = list(map(int, start_ip.split(".")))
   end = list(map(int, end_ip.split(".")))
   temp = start
   ip_range = []
   
   ip_range.append(start_ip)
   while temp != end:
      start[3] += 1
      for i in (3, 2, 1):
         if temp[i] == 256:
            temp[i] = 0
            temp[i-1] += 1
      ip_range.append(".".join(map(str, temp)))    
      
   return ip_range

if __name__ == "__main__":
    ip_set = []
    with open("shellScripts/googleIPs.txt", "r") as doc:
        for line in doc:
            range = line.split("-")
            for add in ips(range[0].strip(), range[1].strip()):
                ip_set.append(add)

    print(len(ip_set))