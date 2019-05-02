require 'json'
require 'aws-sdk-iam'

$iam = Aws::IAM::Client.new

def lambda_handler(event:, context:)
  user_list = $iam.get_group(group_name: ENV['IAM_SSH_GROUP'])
  {
    statusCode: 200,
    body: JSON.generate(user_list.to_h)
  }
end
