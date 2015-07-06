cheerspoints POC
================

> 介接sendgrid API來進行歡樂點(神坊) POC

##Projects

-	Live site: [Cheerspoint](https://mitac-cheerspoint-v20150518.appspot.com/)
-	webmasters: https://mitac-cheerspoint-v20150518.appspot.com/
-	Project Id: **mitac-cheerspoint-v20150518**
-	Project Number: **24182559640**
-	gitlab: (todo)

##Notice

-	目前OAuth login後是以 session 作為登入的檢查，所以 Admin 在後台 修改使用者資料需等到使用者下一次登入時才會套用
-	webapp2 auth_id --> google:{email}, 這個 id 必需是獨一的
-	新增 Account management, Admin 可以預先新增 email/account_enabled/reported_enabled/description. 在使用登入時會自動填入其他資訊
- large CSV parse: GCS client library implement CSV reader iterator.
- webhook module replace '<>' before insert to datastore.
