#!/bin/bash

#      type       : role, tenant, user, token, endpoint, endpointTemplates
#      command    : add, list, disable, delete, grant, revoke

CMD='keystone-manage'

echo "***** TENANT LIST ****"
${CMD} tenant list
tenants=(`${CMD} tenant list | grep -v -e '^id' -e '^--' | awk '{print $2}'`)
# for i in $(seq 0 $((${#tenants[@]} - 1))); do echo ${tenants[i]}; done
echo ""

echo "***** USER LIST ****"
${CMD} user list
users=(`${CMD} user list | grep -v -e '^id' -e '^--' | awk '{print $2}'`)
# for i in $(seq 0 $((${#users[@]} - 1))); do echo ${users[i]}; done
echo ""

echo "***** ROLE LIST ****"
${CMD} role list
echo ""

for i in $(seq 0 $((${#tenants[@]} - 1))); do
  echo "    ** ROLE LIST - TENANT ${tenants[i]} **"
  ${CMD} role list ${tenants[i]}; 
  echo ""
done
echo ""

echo "***** SERVICE LIST ****"
${CMD} service list
echo ""

echo "***** ENDPOINT_TEMPLATES LIST ****"
${CMD} endpointTemplates list
echo ""

echo "***** TOKEN LIST *****"
${CMD} token list
echo ""

echo "***** ENDPOINT LIST *****"
${CMD} endpoint list
echo "FUNCTION DOES NOT EXIST IN KEYSTONE"
echo ""

echo "***** CREDENTIALS LIST *****"
${CMD} credentials list
echo "FUNCTION DOES NOT EXIST IN KEYSTONE"
echo ""
