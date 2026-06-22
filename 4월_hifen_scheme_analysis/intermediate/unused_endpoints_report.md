# Step 6 — Endpoint usage vs frontend

**Backend endpoints:** 636
**Frontend call sites:** 1149
**Frontend files scanned:** 1629

## Usage summary
- CALLED: 453
- UNCALLED: 183

### By confidence
- CALLED/HIGH: 444
- CALLED/MED: 9
- UNCALLED/HIGH: 183

## Per-app breakdown
| app | called | uncalled | uncalled % |
|---|---|---|---|
| admin | 31 | 7 | 18.4% |
| ads | 12 | 11 | 47.8% |
| aichat | 7 | 40 | 85.1% |
| aitools | 0 | 1 | 100.0% |
| amore | 18 | 1 | 5.3% |
| archive | 2 | 9 | 81.8% |
| brand | 16 | 10 | 38.5% |
| creators_insights | 6 | 0 | 0.0% |
| express | 80 | 10 | 11.1% |
| instagram | 36 | 8 | 18.2% |
| instagram_admin | 12 | 1 | 7.7% |
| keywords | 0 | 1 | 100.0% |
| kpi | 14 | 1 | 6.7% |
| monitoring | 9 | 2 | 18.2% |
| oliveyoung | 29 | 9 | 23.7% |
| partner | 42 | 16 | 27.6% |
| partner_admin | 0 | 7 | 100.0% |
| partner_instagram | 3 | 0 | 0.0% |
| preview | 6 | 1 | 14.3% |
| search | 24 | 23 | 48.9% |
| subscribe | 13 | 5 | 27.8% |
| survey | 7 | 0 | 0.0% |
| trends | 11 | 1 | 8.3% |
| user | 26 | 10 | 27.8% |
| youtube | 36 | 9 | 20.0% |
| youtube_shopping | 13 | 0 | 0.0% |

## Sample UNCALLED endpoints (first 30)

- `POST /admin/send-appointment-confirmation` (admin/SendAppointmentConfirmationView)
- `POST /admin/test-brand-detection` (admin/TestBrandDetectionView)
- `POST /admin/test-video-topic-detection` (admin/TestDetectVideoTopicView)
- `POST /admin/google-ads-keyword-test` (admin/GoogleAdsKeywordTestView)
- `GET|PUT /admin/user-management/<int:user_id>` (admin/AdminUserManagementView)
- `POST /admin/user-search` (admin/AdminUserSearchView)
- `GET /admin/user-tracking/<str:report>` (admin/UserTrackingView)
- `POST /ads/top-bumper-from-brand` (ads/TopBumperFromBrandView)
- `POST /ads/create-bumper-cost` (ads/CreateCPMCostView)
- `POST /ads/crawl-waiting-list` (ads/CrawlWaitingListView)
- `POST /ads/detect-on-off-bumper` (ads/DetectOnOffBumperView)
- `POST /ads/search-scene` (ads/BumperSceneSearchView)
- `POST /ads/google-ads-test` (ads/GoogleADsTestView)
- `GET /ads/user-demo-campaign-list` (ads/UserDemoCampaignListView)
- `GET /ads/can-create-campaign` (ads/CanCreateCampaignView)
- `POST /ads/group-display-ad` (ads/GroupDisplayAdView)
- `POST /ads/add-keyword-display-ad` (ads/AddKeywordDisplayAddView)
- `GET /ads/display-ad/<str:unique_id>` (ads/DisplayAdView)
- `POST /aichat/get-video-transcript` (aichat/VideoTranscriptView)
- `POST /aichat/generate-title` (aichat/GenerateTitleView)
- `POST /aichat/generate-description` (aichat/GenerateDescriptionView)
- `POST /aichat/generate-tags` (aichat/GenerateTagsView)
- `POST /aichat/creative` (aichat/CreativeView)
- `POST /aichat/first-videos-keyword` (aichat/FirstVideosKeywordView)
- `POST|PUT /aichat/blog-generation` (aichat/BlogGenerationView)
- `POST /aichat/anthropic-blog-generation` (aichat/AnthropicBlogGenerationView)
- `PUT /aichat/generated-blog-images` (aichat/GeneratedBlogImagesView)
- `POST /aichat/topics-from-title` (aichat/TopicsFromTitleView)
- `DELETE|GET /aichat/chat-history` (aichat/AIChatHistoryView)
- `GET /aichat/previous-messages/<int:chat_history_id>` (aichat/AIPreviousMessagesView)