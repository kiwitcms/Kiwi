# Inspired by https://gitlab.com/gitlab-org/gitlab/-/blob/master/db/fixtures/development/25_api_personal_access_token.rb
# frozen_string_literal: true

token = PersonalAccessToken.new
token.user_id = User.find_by(username: 'root').id
token.name = 'api-token-for-testing'
token.scopes = ["api"]
token.set_token('ypCa3Dzb23o5nvsixwPA')
token.save

print 'OK'
