import random

proxy_list = ['https://51.68.141.240:3128',
              'https://51.158.98.121:8811',
              'https://37.59.158.104:3128',
              'https://103.89.253.246:3128',
              'https://134.119.214.194:8080',
              'https://5.160.218.71:3128',
              'https://188.43.52.166:47362',
              'https://183.89.117.10:8080',
              'https://161.132.101.141:35311']
        
proxy_list = ['https://200.122.209.78:55167',
              'https://82.117.249.87:3128']

proxies = {
    'http': random.choice(proxy_list),
    'https': random.choice(proxy_list)
}
