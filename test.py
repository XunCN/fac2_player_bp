# This script show how to decode and encode blueprint

import base64
import zlib

# encoded blueprint string
bp_str = "0eNqVU9FuwjAM/Bc/TikahcCotC9BqEqLB5bapEtdNoTy73OCoNLGQDQv6dk++y7JCapmwM6TZShOQLWzPRTrE/S0s6aJmDUtQgHGE+9bZKqz2rUVWcPOQ1BAdovfUEyDulEV+dhYvl2Th40CtExMeG6bfo6lHdoKvZCq++0VdK6XamdjT2HMZsvpRCs4yvYtX0ormYC9a8oK9+ZAUiOJI1kp4W0i6GPgg3zP5aiCj11sfiDPgyDXac4ZGZp6H+X0GGnKi1gRpmUG16E359ngRWrdwN3wNLt86o8vubpn8ANX9ET/44vouFox7uVYLmesxKGG0f9GHyjxuBXsU0IiQmDrfJvSZOjO+DR0Ae8JGKJ/86j5ckke0u88on2uwSJsZIV4/77Ip8u3nqo8ro1gxNhKwfg2FBxEdXJUL/LVfLXS8+Usf53pEH4AuTMavg=="
# decode blueprint string
decode_str = zlib.decompress(base64.b64decode(bp_str[1:]))
print(decode_str)
# encode
encode_str = bp_str[0] + str(base64.b64encode(zlib.compress(decode_str, 9)), encoding='utf8')
print(encode_str==bp_str)

