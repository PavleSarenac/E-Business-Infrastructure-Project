# TESTS DESCRIPTION
# python main.py --help

# TESTS WITHOUT BLOCKCHAIN

# python main.py --help
# python main.py --type "authentication" --authentication-url "http://127.0.0.1:5000" --jwt-secret "JWT_SECRET_KEY" --roles-field "roleId" --owner-role "2" --customer-role "1" --courier-role "3"
# python main.py --type "level0" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002"
# python main.py --type "level1" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002"
# python main.py --type "level2" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003"
# python main.py --type "level3" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003"
# python main.py --type "all" --authentication-url "http://127.0.0.1:5000" --jwt-secret "JWT_SECRET_KEY" --roles-field "roleId" --owner-role "2" --customer-role "1" --courier-role "3" --with-authentication --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003"

# TESTS WITH BLOCKCHAIN

python .\initialize_customer_account.py

# python main.py --type "level1" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --with-blockchain --provider-url "http://127.0.0.1:8545" --customer-keys-path "./keys.json" --customer-passphrase "iep_project" --owner-private-key "0x2976743f04a681b2cae92393e5f36b52822880f8fc730a1926c0e6d45eb74a49"
# python main.py --type "level2" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003" --with-blockchain --provider-url "http://127.0.0.1:8545" --customer-keys-path "./keys.json" --customer-passphrase "iep_project" --owner-private-key "0x90d80dc5ad3e9d26d2e8b6e2d6ef88eed9ea7893a391f03f55bc549f3005f532" --courier-private-key "0x651e6c356dad3a06660c696c2c53e8fc3eb13c4427c3f45ba6d2d003be3e9c1c"
# python main.py --type "level3" --with-authentication --authentication-url "http://127.0.0.1:5000" --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003" --with-blockchain --provider-url "http://127.0.0.1:8545" --customer-keys-path "./keys.json" --customer-passphrase "iep_project" --owner-private-key "0xcb8569524a08cef248f777ded2ea1e176df413db51cc4b319a62a16bf2e2ea68" --courier-private-key "0x0986cf8ae8f8fa5e222bd711e1520aacc4bca28fa94ad28fe7d102a7999311a1"
python main.py --type "all" --authentication-url "http://127.0.0.1:5000" --jwt-secret "JWT_SECRET_KEY" --roles-field "roleId" --owner-role "2" --customer-role "1" --courier-role "3" --with-authentication --owner-url "http://127.0.0.1:5001" --customer-url "http://127.0.0.1:5002" --courier-url "http://127.0.0.1:5003" --with-blockchain --provider-url "http://127.0.0.1:8545" --customer-keys-path "./keys.json" --customer-passphrase "iep_project" --owner-private-key "0x451b0972e79c582d87134df92235db43b1cdc026183545ed71a12dce629c6eda" --courier-private-key "0xfa46c0216db178342324cd9229dd307b2d0169cc397684ddcbf9f002c12d7f63"