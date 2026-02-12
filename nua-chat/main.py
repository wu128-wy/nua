# 测试1：亲近模式
curl -X POST https://nua-production.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "我想你了", "user_id": "test"}'

# 测试2：塔罗占卜
curl -X POST https://nua-production.up.railway.app/divination \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "method": "塔罗", "params": [3,7,18], "question": "感情"}'

# 测试3：反馈处理
curl -X POST https://nua-production.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "不准", "user_id": "test"}'
