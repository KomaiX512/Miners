[1mdiff --git a/README.md b/README.md[m
[1mindex 9b51ffe..d775076 100644[m
[1m--- a/README.md[m
[1m+++ b/README.md[m
[36m@@ -126,4 +126,35 @@[m [mgunicorn api:app -b 0.0.0.0:5000[m
 from main import ContentRecommendationSystem[m
 system = ContentRecommendationSystem()[m
 system.process_instagram_username("username", results_limit=50)[m
[31m-```[m
\ No newline at end of file[m
[32m+[m[32m```[m
[32m+[m
[32m+[m[32m## Content Plan Export Functionality[m
[32m+[m
[32m+[m[32mThe system now supports exporting content plan sections to R2 storage with the following directory structure:[m
[32m+[m
[32m+[m[32m### Directory Structure[m
[32m+[m
[32m+[m[32m1. **Competitor Analysis**[m
[32m+[m[32m   - Path: `competitor_analysis/{primary_username}/{competitor_username}/analysis_{n}.json`[m
[32m+[m[32m   - Contains competitor analysis for each competitor with sequential numbering[m
[32m+[m[32m   - Each file includes analysis data and a status field (pending/processed)[m
[32m+[m
[32m+[m[32m2. **Recommendations**[m
[32m+[m[32m   - Path: `recommendations/{primary_username}/recommendation_{n}.json`[m
[32m+[m[32m   - Contains content recommendations with sequential numbering[m
[32m+[m[32m   - Each file includes recommendations, primary analysis, and additional insights with a status field[m
[32m+[m
[32m+[m[32m3. **Next Posts**[m
[32m+[m[32m   - Path: `next_posts/{primary_username}/post_{n}.json`[m
[32m+[m[32m   - Contains next post predictions with sequential numbering[m
[32m+[m[32m   - Each file includes post details (caption, hashtags, visual prompt, etc.) with a status field[m
[32m+[m
[32m+[m[32m### Testing Export Functionality[m
[32m+[m
[32m+[m[32mYou can test the export functionality using the provided test script:[m
[32m+[m
[32m+[m[32m```bash[m
[32m+[m[32mpython test_export.py[m
[32m+[m[32m```[m
[32m+[m
[32m+[m[32mThis will export the content plan sections from the existing `content_plan.json` file to R2 storage following the directory structure described above.[m
\ No newline at end of file[m
[1mdiff --git a/api.py b/api.py[m
[1mindex 9551e93..425bcdd 100644[m
[1m--- a/api.py[m
[1m+++ b/api.py[m
[36m@@ -18,7 +18,14 @@[m [mlogging.basicConfig([m
 logger = logging.getLogger(__name__)[m
 [m
 app = Flask(__name__)[m
[31m-CORS(app)  # Enable CORS for all routes[m
[32m+[m[32m# Configure CORS with specific options[m
[32m+[m[32mCORS(app, resources={[m
[32m+[m[32m    r"/*": {[m
[32m+[m[32m        "origins": "*",[m
[32m+[m[32m        "methods": ["GET", "POST", "OPTIONS"],[m
[32m+[m[32m        "allow_headers": ["Content-Type", "Authorization"][m
[32m+[m[32m    }[m
[32m+[m[32m})[m
 [m
 # Initialize R2 and Instagram scraper[m
 r2_retriever = R2DataRetriever()[m
[36m@@ -27,10 +34,20 @@[m [minstagram_scraper = InstagramScraper()[m
 # Import main module functions instead of the class[m
 import main[m
 [m
[32m+[m[32m@app.after_request[m
[32m+[m[32mdef after_request(response):[m
[32m+[m[32m    """Add CORS headers to every response."""[m
[32m+[m[32m    response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')[m
[32m+[m[32m    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')[m
[32m+[m[32m    return response[m
[32m+[m
 @app.route('/r2/update', methods=['POST', 'OPTIONS'])[m
 def update_r2():[m
     if request.method == 'OPTIONS':[m
[31m-        return '', 204[m
[32m+[m[32m        response = jsonify({'message': 'OK'})[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response[m
         [m
     try:[m
         data = request.get_json()[m
[36m@@ -61,52 +78,67 @@[m [mdef update_r2():[m
             json.dumps(user_data, indent=2)[m
         )[m
         [m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             'success': True,[m
             'message': f'Successfully updated R2 storage for {username}',[m
             'file_path': file_path[m
         })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response[m
         [m
     except Exception as e:[m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             'success': False,[m
             'message': str(e)[m
[31m-        }), 500[m
[32m+[m[32m        })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 500[m
 [m
 @app.route('/scrape', methods=['POST', 'OPTIONS'])[m
 def scrape_profile():[m
     if request.method == 'OPTIONS':[m
[31m-        return '', 204[m
[32m+[m[32m        response = jsonify({'message': 'OK'})[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response[m
         [m
     try:[m
         data = request.get_json()[m
         username = data.get('username')[m
         [m
         if not username:[m
[31m-            return jsonify({[m
[32m+[m[32m            response = jsonify({[m
                 'success': False,[m
                 'message': 'Username is required'[m
[31m-            }), 400[m
[32m+[m[32m            })[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 400[m
             [m
         # Scrape Instagram profile[m
         result = instagram_scraper.scrape_and_upload(username, results_limit=10)[m
         [m
         if result['success']:[m
[31m-            return jsonify({[m
[32m+[m[32m            response = jsonify({[m
                 'success': True,[m
                 'data': result['data'][m
             })[m
         else:[m
[31m-            return jsonify({[m
[32m+[m[32m            response = jsonify({[m
                 'success': False,[m
                 'message': result['message'][m
[31m-            }), 404[m
[32m+[m[32m            })[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 404[m
[32m+[m[41m            [m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response[m
             [m
     except Exception as e:[m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             'success': False,[m
             'message': str(e)[m
[31m-        }), 500[m
[32m+[m[32m        })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 500[m
 [m
 @app.route('/posts/<username>', methods=['GET'])[m
 def get_posts(username):[m
[36m@@ -114,16 +146,20 @@[m [mdef get_posts(username):[m
         # Retrieve posts from R2 storage[m
         posts = r2_retriever.get_posts(username)[m
         [m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             'success': True,[m
             'data': posts[m
         })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response[m
         [m
     except Exception as e:[m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             'success': False,[m
             'message': str(e)[m
[31m-        }), 500[m
[32m+[m[32m        })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 500[m
 [m
 @app.route('/api/analyze', methods=['POST'])[m
 def analyze_profile():[m
[36m@@ -133,40 +169,49 @@[m [mdef analyze_profile():[m
         username = data.get('username')[m
         [m
         if not username:[m
[31m-            return jsonify({"success": False, "message": "Username is required"}), 400[m
[32m+[m[32m            response = jsonify({"success": False, "message": "Username is required"})[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 400[m
         [m
         # First, scrape and upload[m
         scrape_result = instagram_scraper.scrape_and_upload(username)[m
         [m
         if not scrape_result["success"]:[m
[31m-            return jsonify({"success": False, "message": "Failed to scrape profile"}), 500[m
[32m+[m[32m            response = jsonify({"success": False, "message": "Failed to scrape profile"})[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 500[m
         [m
         # Then, run the recommendation pipeline using the main function[m
         object_key = scrape_result["object_key"][m
         [m
         # Call the main function to run the pipeline[m
[31m-        # This assumes your main.py has a function that can be called to run the pipeline[m
         pipeline_result = main.run_pipeline(object_key)[m
         [m
         if not pipeline_result or not pipeline_result.get("success", False):[m
[31m-            return jsonify({[m
[32m+[m[32m            response = jsonify({[m
                 "success": False, [m
                 "message": "Failed to generate recommendations",[m
                 "details": pipeline_result[m
[31m-            }), 500[m
[32m+[m[32m            })[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 500[m
         [m
         # Return success with content plan[m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             "success": True,[m
             "message": "Successfully generated recommendations",[m
             "details": pipeline_result[m
[31m-        }), 200[m
[32m+[m[32m        })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 200[m
         [m
     except Exception as e:[m
         logger.error(f"Error in analyze_profile: {str(e)}")[m
         import traceback[m
         logger.error(traceback.format_exc())[m
[31m-        return jsonify({"success": False, "message": str(e)}), 500[m
[32m+[m[32m        response = jsonify({"success": False, "message": str(e)})[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 500[m
 [m
 @app.route('/api/content_plan', methods=['GET'])[m
 def get_content_plan():[m
[36m@@ -174,23 +219,29 @@[m [mdef get_content_plan():[m
     try:[m
         # Check if content plan file exists[m
         if not os.path.exists('content_plan.json'):[m
[31m-            return jsonify({[m
[32m+[m[32m            response = jsonify({[m
                 "success": False,[m
                 "message": "No content plan available"[m
[31m-            }), 404[m
[32m+[m[32m            })[m
[32m+[m[32m            response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m            return response, 404[m
             [m
         # Load the content plan from file[m
         with open('content_plan.json', 'r') as f:[m
             content_plan = json.load(f)[m
         [m
[31m-        return jsonify({[m
[32m+[m[32m        response = jsonify({[m
             "success": True,[m
             "content_plan": content_plan[m
[31m-        }), 200[m
[32m+[m[32m        })[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 200[m
         [m
     except Exception as e:[m
         logger.error(f"Error in get_content_plan: {str(e)}")[m
[31m-        return jsonify({"success": False, "message": str(e)}), 500[m
[32m+[m[32m        response = jsonify({"success": False, "message": str(e)})[m
[32m+[m[32m        response.headers.add('Access-Control-Allow-Origin', '*')[m
[32m+[m[32m        return response, 500[m
 [m
 if __name__ == "__main__":[m
[31m-    app.run(debug=True, port=5000) [m
\ No newline at end of file[m
[32m+[m[32m    app.run(debug=True, port=5000)[m
\ No newline at end of file[m
[1mdiff --git a/config.py b/config.py[m
[1mindex 691b7f6..2f88cea 100644[m
[1m--- a/config.py[m
[1m+++ b/config.py[m
[36m@@ -2,9 +2,9 @@[m
 [m
 # R2 Storage Configuration[m
 R2_CONFIG = {[m
[31m-    'endpoint_url': f'https://51abf57b5c6f9b6cf2f91cc87e0b9ffe.r2.cloudflarestorage.com',[m
[31m-    'aws_access_key_id': '2093fa05ee0323bb39de512a19638e78',[m
[31m-    'aws_secret_access_key': 'e9e7173d1ee514b452b3a3eb7cef6fb57a248423114f1f949d71dabd34eee04f',[m
[32m+[m[32m    'endpoint_url': f'https://9069781eea9a108d41848d73443b3a87.r2.cloudflarestorage.com',[m
[32m+[m[32m    'aws_access_key_id': 'b94be077bc48dcc2aec3e4331233327e',[m
[32m+[m[32m    'aws_secret_access_key': '791d5eeddcd8ed5bf3f41bfaebbd37e58af7dcb12275b1422747605d7dc75bc4',[m
     'bucket_name': 'structuredb',[m
     'bucket_name2': 'tasks'[m
 }[m
[36m@@ -26,7 +26,10 @@[m [mVECTOR_DB_CONFIG = {[m
 GEMINI_CONFIG = {[m
     'api_key': 'AIzaSyDrvJG2BghzqtSK-HIZ_NsfRWiNwrIk3DQ',[m
     'model': 'gemini-2.0-flash',[m
[31m-    'max_tokens': 200[m
[32m+[m[32m    'max_tokens': 2000,[m
[32m+[m[32m    'temperature': 0.2,  # Lower temperature for more focused, analytical responses[m
[32m+[m[32m    'top_p': 0.95,       # Slightly more deterministic for business analysis[m
[32m+[m[32m    'top_k': 40          # Broader selection of tokens for more detailed responses[m
 }[m
 [m
 # Content Templates[m
[1mdiff --git a/data_retrieval.py b/data_retrieval.py[m
[1mindex c93b467..14b71d1 100644[m
[1m--- a/data_retrieval.py[m
[1m+++ b/data_retrieval.py[m
[36m@@ -37,12 +37,15 @@[m [mclass R2DataRetriever:[m
             raise[m
     [m
     @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))[m
[31m-    def list_objects(self):[m
[31m-        """List objects in the R2 bucket."""[m
[32m+[m[32m    def list_objects(self, prefix=None):[m
[32m+[m[32m        """List objects in the R2 bucket, optionally filtered by prefix."""[m
         try:[m
[31m-            response = self.client.list_objects_v2(Bucket=self.config['bucket_name'])[m
[32m+[m[32m            params = {'Bucket': self.config['bucket_name']}[m
[32m+[m[32m            if prefix:[m
[32m+[m[32m                params['Prefix'] = prefix[m
[32m+[m[32m            response = self.client.list_objects_v2(**params)[m
             objects = response.get('Contents', [])[m
[31m-            logger.info(f"Found {len(objects)} objects in bucket")[m
[32m+[m[32m            logger.info(f"Found {len(objects)} objects in bucket with prefix '{prefix or ''}'")[m
             return objects[m
         except Exception as e:[m
             logger.error(f"Error listing objects: {str(e)}")[m
[36m@@ -72,11 +75,87 @@[m [mclass R2DataRetriever:[m
             return data[m
         except Exception as e:[m
             logger.error(f"Error parsing JSON from {key}: {str(e)}")[m
[31m-            return None  # Return None instead of {}[m
[32m+[m[32m            return None[m
     [m
[31m-    def get_social_media_data(self, key='humansofny/humansofny_20250404_112030.json'):[m
[31m-        """Get social media data specifically."""[m
[31m-        return self.get_json_data(key)[m
[32m+[m[32m    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))[m
[32m+[m[32m    def put_object(self, key, content=None):[m
[32m+[m[32m        """Put an object into the R2 bucket.[m
[32m+[m[41m        [m
[32m+[m[32m        Args:[m
[32m+[m[32m            key (str): The key (filename) to use in R2[m
[32m+[m[32m            content (str, optional): Content to put in the object, if None creates an empty object (e.g., for directory markers)[m
[32m+[m[41m            [m
[32m+[m[32m        Returns:[m
[32m+[m[32m            bool: True if successful, False otherwise[m
[32m+[m[32m        """[m
[32m+[m[32m        try:[m
[32m+[m[32m            params = {[m
[32m+[m[32m                'Bucket': self.config['bucket_name'],[m
[32m+[m[32m                'Key': key[m
[32m+[m[32m            }[m
[32m+[m[41m            [m
[32m+[m[32m            if content is not None:[m
[32m+[m[32m                if isinstance(content, str):[m
[32m+[m[32m                    params['Body'] = content[m
[32m+[m[32m                else:[m
[32m+[m[32m                    params['Body'] = json.dumps(content)[m
[32m+[m[41m            [m
[32m+[m[32m            self.client.put_object(**params)[m
[32m+[m[32m            logger.info(f"Successfully put object at {key}")[m
[32m+[m[32m            return True[m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            logger.error(f"Error putting object at {key}: {str(e)}")[m
[32m+[m[32m            return False[m
[32m+[m[41m    [m
[32m+[m[32m    def get_social_media_data(self, primary_username):[m
[32m+[m[32m        """[m
[32m+[m[32m        Get social media data for a primary username and its competitors.[m
[32m+[m[41m        [m
[32m+[m[32m        Args:[m
[32m+[m[32m            primary_username (str): The primary Instagram username (e.g., 'maccosmetics')[m
[32m+[m[41m            [m
[32m+[m[32m        Returns:[m
[32m+[m[32m            list: Combined list of post data from primary and competitor files, or None if failed[m
[32m+[m[32m        """[m
[32m+[m[32m        try:[m
[32m+[m[32m            # Define the prefix for the primary username's directory[m
[32m+[m[32m            prefix = f"{primary_username}/"[m
[32m+[m[32m            logger.info(f"Retrieving social media data for {primary_username} with prefix '{prefix}'")[m
[32m+[m[41m            [m
[32m+[m[32m            # List all objects under the primary username's directory[m
[32m+[m[32m            objects = self.list_objects(prefix=prefix)[m
[32m+[m[32m            if not objects:[m
[32m+[m[32m                logger.warning(f"No objects found under prefix '{prefix}'")[m
[32m+[m[32m                return None[m
[32m+[m[41m            [m
[32m+[m[32m            combined_data = [][m
[32m+[m[32m            primary_key = f"{primary_username}/{primary_username}.json"[m
[32m+[m[32m            found_primary = False[m
[32m+[m[41m            [m
[32m+[m[32m            # Retrieve and combine data from all relevant files[m
[32m+[m[32m            for obj in objects:[m
[32m+[m[32m                key = obj['Key'][m
[32m+[m[32m                if key.endswith('.json'):  # Only process JSON files[m
[32m+[m[32m                    data = self.get_json_data(key)[m
[32m+[m[32m                    if data:[m
[32m+[m[32m                        if key == primary_key:[m
[32m+[m[32m                            found_primary = True[m
[32m+[m[32m                        combined_data.extend(data)  # Assuming data is a list of posts[m
[32m+[m[41m            [m
[32m+[m[32m            if not found_primary:[m
[32m+[m[32m                logger.warning(f"Primary file '{primary_key}' not found")[m
[32m+[m[32m                return None[m
[32m+[m[41m                [m
[32m+[m[32m            if not combined_data:[m
[32m+[m[32m                logger.warning(f"No valid data retrieved for {primary_username}")[m
[32m+[m[32m                return None[m
[32m+[m[41m                [m
[32m+[m[32m            logger.info(f"Successfully retrieved {len(combined_data)} posts for {primary_username} and competitors")[m
[32m+[m[32m            return combined_data[m
[32m+[m[41m            [m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            logger.error(f"Error retrieving social media data for {primary_username}: {str(e)}")[m
[32m+[m[32m            return None[m
 [m
     def upload_file(self, key, file_obj):[m
         """[m
[36m@@ -100,20 +179,19 @@[m [mclass R2DataRetriever:[m
 [m
 # Function to test the data retrieval[m
 def test_connection():[m
[31m-    """Test connection to R2 and basic retrieval."""[m
[32m+[m[32m    """Test connection to R2 and multi-file retrieval."""[m
     try:[m
         retriever = R2DataRetriever()[m
[31m-        objects = retriever.list_objects()[m
[32m+[m[32m        # Test with a sample primary username[m
[32m+[m[32m        primary_username = "maccosmetics"[m
[32m+[m[32m        logger.info(f"Testing retrieval for primary username: {primary_username}")[m
         [m
[31m-        if objects:[m
[31m-            sample_key = objects[0]['Key'][m
[31m-            logger.info(f"Testing retrieval with object: {sample_key}")[m
[31m-            response = retriever.get_object(sample_key)[m
[31m-            size = response['ContentLength'][m
[31m-            logger.info(f"Successfully retrieved {sample_key} ({size} bytes)")[m
[32m+[m[32m        data = retriever.get_social_media_data(primary_username)[m
[32m+[m[32m        if data:[m
[32m+[m[32m            logger.info(f"Successfully retrieved {len(data)} posts for {primary_username}")[m
             return True[m
         else:[m
[31m-            logger.warning("No objects found in bucket")[m
[32m+[m[32m            logger.warning(f"No data retrieved for {primary_username}")[m
             return False[m
             [m
     except Exception as e:[m
[1mdiff --git a/instagram_scraper.py b/instagram_scraper.py[m
[1mindex 19792b1..c129e61 100644[m
[1m--- a/instagram_scraper.py[m
[1m+++ b/instagram_scraper.py[m
[36m@@ -1,9 +1,9 @@[m
 """Module for scraping Instagram profiles and uploading to R2 storage."""[m
[31m-[m
 import time[m
 import json[m
 import os[m
 import logging[m
[32m+[m[32mimport shutil[m
 import boto3[m
 from botocore.client import Config[m
 from botocore.exceptions import ClientError[m
[36m@@ -28,6 +28,14 @@[m [mclass InstagramScraper:[m
         """Initialize with API token and R2 configuration."""[m
         self.api_token = api_token[m
         self.r2_config = r2_config  # Assumes R2_CONFIG is set for "structuredb"[m
[32m+[m[32m        # Initialize S3 client[m
[32m+[m[32m        self.s3 = boto3.client([m
[32m+[m[32m            's3',[m
[32m+[m[32m            endpoint_url=self.r2_config['endpoint_url'],[m
[32m+[m[32m            aws_access_key_id=self.r2_config['aws_access_key_id'],[m
[32m+[m[32m            aws_secret_access_key=self.r2_config['aws_secret_access_key'],[m
[32m+[m[32m            config=Config(signature_version='s3v4')[m
[32m+[m[32m        )[m
     [m
     def scrape_profile(self, username, results_limit=10):[m
         """[m
[36m@@ -71,14 +79,35 @@[m [mclass InstagramScraper:[m
             logger.error(f"Error scraping {username}: {str(e)}")[m
             return None[m
     [m
[31m-    def save_to_local_file(self, data, username):[m
[32m+[m[32m    def create_local_directory(self, directory_name):[m
         """[m
[31m-        Save scraped data to a local file.[m
[32m+[m[32m        Create a local directory for storing scraped files.[m
         [m
         Args:[m
[31m-            data (list): Scraped data[m
[31m-            username (str): Instagram username[m
[32m+[m[32m            directory_name (str): Name of the directory to create[m
[32m+[m[41m            [m
[32m+[m[32m        Returns:[m
[32m+[m[32m            str: Path to the created directory or None if failed[m
[32m+[m[32m        """[m
[32m+[m[32m        try:[m
[32m+[m[32m            # Create directory in the temp folder[m
[32m+[m[32m            dir_path = os.path.join('temp', directory_name)[m
[32m+[m[32m            os.makedirs(dir_path, exist_ok=True)[m
[32m+[m[32m            logger.info(f"Created local directory: {dir_path}")[m
[32m+[m[32m            return dir_path[m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            logger.error(f"Error creating local directory: {str(e)}")[m
[32m+[m[32m            return None[m
[32m+[m[41m    [m
[32m+[m[32m    def save_to_local_file(self, data, directory_path, filename):[m
[32m+[m[32m        """[m
[32m+[m[32m        Save scraped data to local file within the specified directory.[m
         [m
[32m+[m[32m        Args:[m
[32m+[m[32m            data: The scraped data to save[m
[32m+[m[32m            directory_path (str): Path to the directory to save in[m
[32m+[m[32m            filename (str): The filename to save the data as[m
[32m+[m[41m            [m
         Returns:[m
             str: Path to the saved file or None if failed[m
         """[m
[36m@@ -86,141 +115,256 @@[m [mclass InstagramScraper:[m
             logger.warning("No data to save to local file")[m
             return None[m
         [m
[31m-        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")[m
[31m-        filename = f"{username}_{timestamp}.json"[m
[31m-        [m
         try:[m
[31m-            with open(filename, 'w', encoding='utf-8') as f:[m
[32m+[m[32m            # Ensure directory exists[m
[32m+[m[32m            os.makedirs(directory_path, exist_ok=True)[m
[32m+[m[32m            file_path = os.path.join(directory_path, filename)[m
[32m+[m[41m            [m
[32m+[m[32m            with open(file_path, 'w', encoding='utf-8') as f:[m
                 json.dump(data, f, ensure_ascii=False, indent=4)[m
[31m-            logger.info(f"Data saved to local file: {filename}")[m
[31m-            return filename[m
[32m+[m[32m            logger.info(f"Data saved to local file: {file_path}")[m
[32m+[m[32m            return file_path[m
         except Exception as e:[m
             logger.error(f"Error saving data to local file: {str(e)}")[m
             return None[m
     [m
[31m-    def upload_to_r2(self, local_file_path, username):[m
[32m+[m[32m    def upload_directory_to_r2(self, local_directory, r2_prefix):[m
         """[m
[31m-        Upload file to Cloudflare R2 storage ("structuredb").[m
[32m+[m[32m        Upload an entire directory to R2 storage.[m
         [m
         Args:[m
[31m-            local_file_path (str): Path to local file[m
[31m-            username (str): Instagram username[m
[31m-        [m
[32m+[m[32m            local_directory (str): Path to the local directory[m
[32m+[m[32m            r2_prefix (str): Prefix to use in R2 bucket[m
[32m+[m[41m            [m
         Returns:[m
[31m-            str: Object key in R2 bucket or None if failed[m
[32m+[m[32m            bool: True if successful, False otherwise[m
         """[m
[31m-        if not local_file_path:[m
[31m-            logger.warning("No local file path provided for R2 upload")[m
[31m-            return None[m
[31m-        [m
[31m-        try:[m
[31m-            s3 = boto3.client([m
[31m-                's3',[m
[31m-                endpoint_url=self.r2_config['endpoint_url'],[m
[31m-                aws_access_key_id=self.r2_config['aws_access_key_id'],[m
[31m-                aws_secret_access_key=self.r2_config['aws_secret_access_key'],[m
[31m-                config=Config(signature_version='s3v4')[m
[31m-            )[m
[31m-            [m
[31m-            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")[m
[31m-            object_key = f"{username}/{username}_{timestamp}.json"[m
[32m+[m[32m        if not os.path.exists(local_directory):[m
[32m+[m[32m            logger.error(f"Local directory does not exist: {local_directory}")[m
[32m+[m[32m            return False[m
             [m
[31m-            s3.upload_file([m
[31m-                local_file_path,[m
[31m-                self.r2_config['bucket_name'],  # "structuredb"[m
[31m-                object_key[m
[32m+[m[32m        try:[m
[32m+[m[32m            # First create a directory marker[m
[32m+[m[32m            self.s3.put_object([m
[32m+[m[32m                Bucket=self.r2_config['bucket_name'],[m
[32m+[m[32m                Key=f"{r2_prefix}/"[m
             )[m
[32m+[m[32m            logger.info(f"Created directory marker in R2: {r2_prefix}/")[m
             [m
[31m-            logger.info(f"Uploaded to R2 bucket {self.r2_config['bucket_name']} with key: {object_key}")[m
[32m+[m[32m            uploaded_files = [][m
             [m
[31m-            try:[m
[31m-                os.remove(local_file_path)[m
[31m-                logger.info(f"Removed local file: {local_file_path}")[m
[31m-            except Exception as e:[m
[31m-                logger.warning(f"Failed to remove local file {local_file_path}: {str(e)}")[m
[32m+[m[32m            # Upload all files in the directory[m
[32m+[m[32m            for filename in os.listdir(local_directory):[m
[32m+[m[32m                local_file_path = os.path.join(local_directory, filename)[m
[32m+[m[41m                [m
[32m+[m[32m                # Skip directories[m
[32m+[m[32m                if os.path.isdir(local_file_path):[m
[32m+[m[32m                    continue[m
[32m+[m[41m                    [m
[32m+[m[32m                # Upload file[m
[32m+[m[32m                object_key = f"{r2_prefix}/{filename}"[m
[32m+[m[32m                self.s3.upload_file([m
[32m+[m[32m                    local_file_path,[m
[32m+[m[32m                    self.r2_config['bucket_name'],[m
[32m+[m[32m                    object_key,[m
[32m+[m[32m                    ExtraArgs={'ContentType': 'application/json'}[m
[32m+[m[32m                )[m
[32m+[m[32m                logger.info(f"Uploaded file to R2: {object_key}")[m
[32m+[m[32m                uploaded_files.append(object_key)[m
             [m
[31m-            return object_key[m
[32m+[m[32m            logger.info(f"Successfully uploaded directory to R2: {r2_prefix}/")[m
[32m+[m[32m            return True[m
         except Exception as e:[m
[31m-            logger.error(f"Error uploading to R2: {str(e)}")[m
[31m-            return None[m
[32m+[m[32m            logger.error(f"Failed to upload directory to R2: {str(e)}")[m
[32m+[m[32m            return False[m
     [m
[31m-    def scrape_and_upload(self, username, results_limit=10):[m
[32m+[m[32m    def process_account_batch(self, parent_username, competitor_usernames, results_limit=10):[m
         """[m
[31m-        Scrape Instagram profile and upload to R2 in one operation.[m
[32m+[m[32m        Process a parent account and its competitors, saving all files locally first.[m
         [m
[32m+[m[32m        Args:[m
[32m+[m[32m            parent_username (str): Username of the parent account[m
[32m+[m[32m            competitor_usernames (list): List of competitor usernames[m
[32m+[m[32m            results_limit (int): Maximum results to fetch[m
[32m+[m[41m            [m
         Returns:[m
[31m-            dict: Result with success status, message, and object_key[m
[32m+[m[32m            dict: Result with success status and message[m
         """[m
[31m-        logger.info(f"Starting scrape and upload for {username}")[m
[32m+[m[32m        logger.info(f"Processing account batch for: {parent_username}")[m
         [m
[31m-        data = self.scrape_profile(username, results_limit)[m
[31m-        if not data:[m
[31m-            return {"success": False, "message": "Failed to scrape profile"}[m
[32m+[m[32m        # Create temp directory if it doesn't exist[m
[32m+[m[32m        os.makedirs('temp', exist_ok=True)[m
         [m
[31m-        local_file_path = self.save_to_local_file(data, username)[m
[31m-        if not local_file_path:[m
[31m-            return {"success": False, "message": "Failed to save data to local file"}[m
[32m+[m[32m        # Create local directory for the parent account[m
[32m+[m[32m        local_dir = self.create_local_directory(parent_username)[m
[32m+[m[32m        if not local_dir:[m
[32m+[m[32m            return {"success": False, "message": f"Failed to create local directory for {parent_username}"}[m
         [m
[31m-        object_key = self.upload_to_r2(local_file_path, username)[m
[31m-        if not object_key:[m
[31m-            return {"success": False, "message": "Failed to upload data to R2"}[m
[32m+[m[32m        # Scrape and save parent profile[m
[32m+[m[32m        parent_data = self.scrape_profile(parent_username, results_limit)[m
[32m+[m[32m        if not parent_data:[m
[32m+[m[32m            return {"success": False, "message": f"Failed to scrape parent profile: {parent_username}"}[m
         [m
[31m-        logger.info(f"Completed scrape and upload for {username}")[m
[31m-        return {[m
[31m-            "success": True,[m
[31m-            "message": "Pipeline completed successfully",[m
[31m-            "object_key": object_key[m
[32m+[m[32m        # Save parent data to local file[m
[32m+[m[32m        parent_file = f"{parent_username}.json"[m
[32m+[m[32m        parent_path = self.save_to_local_file(parent_data, local_dir, parent_file)[m
[32m+[m[32m        if not parent_path:[m
[32m+[m[32m            return {"success": False, "message": f"Failed to save parent data locally: {parent_username}"}[m
[32m+[m[41m        [m
[32m+[m[32m        # Process competitor accounts (up to 5)[m
[32m+[m[32m        for competitor in competitor_usernames[:5]:[m
[32m+[m[32m            # Scrape competitor profile[m
[32m+[m[32m            competitor_data = self.scrape_profile(competitor, results_limit)[m
[32m+[m[32m            if not competitor_data:[m
[32m+[m[32m                logger.warning(f"Failed to scrape competitor profile: {competitor}")[m
[32m+[m[32m                continue[m
[32m+[m[41m            [m
[32m+[m[32m            # Save competitor data to local file[m
[32m+[m[32m            competitor_file = f"{competitor}.json"[m
[32m+[m[32m            competitor_path = self.save_to_local_file(competitor_data, local_dir, competitor_file)[m
[32m+[m[32m            if not competitor_path:[m
[32m+[m[32m                logger.warning(f"Failed to save competitor data locally: {competitor}")[m
[32m+[m[32m                continue[m
[32m+[m[41m                [m
[32m+[m[32m            logger.info(f"Successfully processed competitor: {competitor}")[m
[32m+[m[41m        [m
[32m+[m[32m        # Upload entire directory to R2[m
[32m+[m[32m        if self.upload_directory_to_r2(local_dir, parent_username):[m
[32m+[m[32m            # Clean up local directory[m
[32m+[m[32m            try:[m
[32m+[m[32m                shutil.rmtree(local_dir)[m
[32m+[m[32m                logger.info(f"Removed local directory: {local_dir}")[m
[32m+[m[32m            except Exception as e:[m
[32m+[m[32m                logger.warning(f"Failed to remove local directory {local_dir}: {str(e)}")[m
[32m+[m[41m                [m
[32m+[m[32m            return {[m
[32m+[m[32m                "success": True,[m
[32m+[m[32m                "message": f"Successfully processed account batch for: {parent_username}"[m
[32m+[m[32m            }[m
[32m+[m[32m        else:[m
[32m+[m[32m            return {"success": False, "message": f"Failed to upload directory to R2: {parent_username}"}[m
[32m+[m[41m    [m
[32m+[m[32m    def verify_structure(self, parent_username):[m
[32m+[m[32m        """[m
[32m+[m[32m        Verify the directory structure for a parent account.[m
[32m+[m[41m        [m
[32m+[m[32m        Args:[m
[32m+[m[32m            parent_username (str): Username of the parent account[m
[32m+[m[41m            [m
[32m+[m[32m        Returns:[m
[32m+[m[32m            dict: Status of each file in the structure[m
[32m+[m[32m        """[m
[32m+[m[32m        structure = {[m
[32m+[m[32m            f"{parent_username}/{parent_username}.json": False,[m
         }[m
[32m+[m[41m        [m
[32m+[m[32m        # Add competitor files to structure[m
[32m+[m[32m        for i in range(1, 6):[m
[32m+[m[32m            structure[f"{parent_username}/competitor{i}.json"] = False[m
[32m+[m[41m        [m
[32m+[m[32m        try:[m
[32m+[m[32m            # List all objects in the parent directory[m
[32m+[m[32m            response = self.s3.list_objects_v2([m
[32m+[m[32m                Bucket=self.r2_config['bucket_name'],[m
[32m+[m[32m                Prefix=f"{parent_username}/"[m
[32m+[m[32m            )[m
[32m+[m[41m            [m
[32m+[m[32m            if 'Contents' in response:[m
[32m+[m[32m                for item in response['Contents']:[m
[32m+[m[32m                    key = item['Key'][m
[32m+[m[32m                    if key in structure:[m
[32m+[m[32m                        structure[key] = True[m
[32m+[m[41m            [m
[32m+[m[32m            missing = [k for k, v in structure.items() if not v][m
[32m+[m[32m            if missing:[m
[32m+[m[32m                logger.warning(f"Missing files in structure for {parent_username}: {missing}")[m
[32m+[m[32m            else:[m
[32m+[m[32m                logger.info(f"Complete structure verified for {parent_username}")[m
[32m+[m[41m                [m
[32m+[m[32m            return structure[m
[32m+[m[32m        except Exception as e:[m
[32m+[m[32m            logger.error(f"Failed to verify structure: {str(e)}")[m
[32m+[m[32m            return structure[m
     [m
     def retrieve_and_process_usernames(self):[m
         """[m
[31m-        Retrieve pending usernames from "tasks" bucket, process them, and update statuses.[m
[31m-        Returns list of processed object keys.[m
[32m+[m[32m        Retrieve ONE pending username from "tasks" bucket, process it with its competitors,[m
[32m+[m[32m        and update its status. Returns the processed parent username or an empty list if none processed.[m
[32m+[m[41m        [m
[32m+[m[32m        This implements a sequential queue processing system to ensure hierarchies don't mix.[m
[32m+[m[32m        Only one primary username (with its children) is processed in each call.[m
         """[m
         usernames_bucket = "tasks"[m
         usernames_key = "Usernames/instagram.json"[m
[31m-        processed_keys = [][m
[31m-        [m
[31m-        s3 = boto3.client([m
[31m-            's3',[m
[31m-            endpoint_url=self.r2_config['endpoint_url'],[m
[31m-            aws_access_key_id=self.r2_config['aws_access_key_id'],[m
[31m-            aws_secret_access_key=self.r2_config['aws_secret_access_key'],[m
[31m-            config=Config(signature_version='s3v4')[m
[31m-        )[m
[32m+[m[32m        processed_parents = [][m
         [m
         try:[m
[31m-            response = s3.get_object(Bucket=usernames_bucket, Key=usernames_key)[m
[32m+[m[32m            # Get usernames from tasks bucket[m
[32m+[m[32m            response = self.s3.get_object(Bucket=usernames_bucket, Key=usernames_key)[m
             usernames_data = json.loads(response['Body'].read().decode('utf-8'))[m
         except ClientError as e:[m
             if e.response['Error']['Code'] == "NoSuchKey":[m
                 logger.info("No usernames file found in 'tasks' bucket")[m
[31m-                return processed_keys[m
[32m+[m[32m                return processed_parents[m
             logger.error(f"Failed to retrieve usernames from R2: {str(e)}")[m
[31m-            return processed_keys[m
[32m+[m[32m            return processed_parents[m
         except Exception as e:[m
             logger.error(f"Failed to retrieve usernames from R2: {str(e)}")[m
[31m-            return processed_keys[m
[31m-[m
[32m+[m[32m            return processed_parents[m
[32m+[m[41m            [m
[32m+[m[32m        # Sort entries by timestamp to process oldest first[m
[32m+[m[32m        if usernames_data:[m
[32m+[m[32m            usernames_data.sort(key=lambda x: x.get('timestamp', ''))[m
[32m+[m[41m        [m
         updated = False[m
[32m+[m[32m        # Process only ONE pending parent username[m
         for entry in usernames_data:[m
             if entry.get('status') == 'pending':[m
[31m-                username = entry['username'][m
[31m-                logger.info(f"Processing username: {username}")[m
[31m-                result = self.scrape_and_upload(username)[m
[32m+[m[32m                parent_username = entry['username'][m
[32m+[m[32m                logger.info(f"Processing single parent username from queue: {parent_username}")[m
[32m+[m[41m                [m
[32m+[m[32m                # Get competitor usernames[m
[32m+[m[32m                competitor_usernames = [][m
[32m+[m[32m                for child in entry.get('children', []):[m
[32m+[m[32m                    if child.get('status') == 'pending' and len(competitor_usernames) < 5:[m
[32m+[m[32m                        competitor_usernames.append(child['username'])[m
[32m+[m[41m                [m
[32m+[m[32m                # Process parent and competitor accounts as a batch[m
[32m+[m[32m                result = self.process_account_batch(parent_username, competitor_usernames)[m
                 [m
                 if result['success']:[m
[32m+[m[32m                    # Update parent status[m
                     entry['status'] = 'processed'[m
                     entry['processed_at'] = datetime.now().isoformat()[m
[31m-                    processed_keys.append(result['object_key'])[m
[32m+[m[32m                    processed_parents.append(parent_username)[m
                     updated = True[m
[31m-                    logger.info(f"Successfully processed {username}")[m
[32m+[m[41m                    [m
[32m+[m[32m                    # Update competitor statuses[m
[32m+[m[32m                    for idx, child in enumerate(entry.get('children', [])):[m
[32m+[m[32m                        if idx < len(competitor_usernames) and child['username'] == competitor_usernames[idx]:[m
[32m+[m[32m                            child['status'] = 'processed'[m
[32m+[m[32m                            child['processed_at'] = datetime.now().isoformat()[m
[32m+[m[41m                    [m
[32m+[m[32m                    # Verify structure[m
[32m+[m[32m                    structure_status = self.verify_structure(parent_username)[m
[32m+[m[32m                    entry['structure_verified'] = all(structure_status.values())[m
[32m+[m[41m                    [m
[32m+[m[32m                    # Break after processing ONE parent username - this ensures sequential processing[m
[32m+[m[32m                    logger.info(f"Queue system: Completed processing {parent_username}. Exiting queue processing.")[m
[32m+[m[32m                    break[m
                 else:[m
[31m-                    logger.warning(f"Failed to process {username}: {result['message']}")[m
[31m-[m
[32m+[m[32m                    logger.error(f"Failed to process parent username {parent_username}: {result.get('message')}")[m
[32m+[m[32m                    # Mark as failed to prevent repeated processing attempts[m
[32m+[m[32m                    entry['status'] = 'failed'[m
[32m+[m[32m                    entry['error'] = result.get('message', 'Unknown error')[m
[32m+[m[32m                    entry['failed_at'] = datetime.now().isoformat()[m
[32m+[m[32m                    updated = True[m
[32m+[m[32m                    # Don't break here so we can try the next pending username[m
[32m+[m[41m        [m
[32m+[m[32m        # Update statuses in tasks bucket[m
         if updated:[m
             try:[m
[31m-                s3.put_object([m
[32m+[m[32m                self.s3.put_object([m
                     Bucket=usernames_bucket,[m
                     Key=usernames_key,[m
                     Body=json.dumps(usernames_data, indent=4),[m
[36m@@ -229,25 +373,39 @@[m [mclass InstagramScraper:[m
                 logger.info("Updated usernames status in 'tasks' bucket")[m
             except Exception as e:[m
                 logger.error(f"Failed to update usernames in R2: {str(e)}")[m
[31m-[m
[31m-        return processed_keys[m
[32m+[m[41m                [m
[32m+[m[32m        return processed_parents[m
 [m
 def test_instagram_scraper():[m
[31m-    """Test the Instagram scraper with a single username."""[m
[32m+[m[32m    """Test the Instagram scraper with a single account and its competitors."""[m
     try:[m
         scraper = InstagramScraper()[m
[31m-        test_username = "humansofny"[m
[31m-        result = scraper.scrape_and_upload(test_username, results_limit=5)[m
         [m
[31m-        if result["success"]:[m
[31m-            logger.info(f"Test successful: {result['message']}")[m
[31m-            return True[m
[31m-        logger.warning(f"Test failed: {result['message']}")[m
[31m-        return False[m
[32m+[m[32m        # Test with parent account and 2 competitors[m
[32m+[m[32m        parent_username = "humansofny"[m
[32m+[m[32m        competitors = ["natgeo", "instagram"][m
[32m+[m[41m        [m
[32m+[m[32m        # Process entire batch[m
[32m+[m[32m        result = scraper.process_account_batch(parent_username, competitors, results_limit=5)[m
[32m+[m[32m        if not result["success"]:[m
[32m+[m[32m            logger.error(f"Test failed: {result['message']}")[m
[32m+[m[32m            return False[m
[32m+[m[41m            [m
[32m+[m[32m        # Verify the structure[m
[32m+[m[32m        structure_status = scraper.verify_structure(parent_username)[m
[32m+[m[32m        if not all([structure_status.get(f"{parent_username}/{parent_username}.json"),[m[41m [m
[32m+[m[32m                   structure_status.get(f"{parent_username}/competitor1.json"),[m
[32m+[m[32m                   structure_status.get(f"{parent_username}/competitor2.json")]):[m
[32m+[m[32m            logger.error(f"Test failed: Structure verification failed")[m
[32m+[m[32m            return False[m
[32m+[m[41m        [m
[32m+[m[32m        logger.info("Test successful: All accounts processed correctly with proper directory structure")[m
[32m+[m[32m        return True[m
     except Exception as e:[m
         logger.error(f"Test failed with exception: {str(e)}")[m
         return False[m
 [m
 if __name__ == "__main__":[m
     scraper = InstagramScraper()[m
[31m-    scraper.retrieve_and_process_usernames()[m
\ No newline at end of file[m
[32m+[m[32m    processed = scraper.retrieve_and_process_usernames()[m
[32m+[m[32m    logger.info(f"Processed {len(processed)} parent accounts")[m
\ No newline at end of file[m
[1mdiff --git a/main.py b/main.py[m
[1mindex b3fc05f..160ed1e 100644[m
[1m--- a/main.py[m
[1m+++ b/main.py[m
[36m@@ -3,7 +3,7 @@[m
 import logging[m
 import json[m
 import os[m
[31m-import io  # <-- Added import for io module[m
[32m+[m[32mimport io[m
 from datetime import datetime[m
 from data_retrieval import R2DataRetriever[m
 from time_series_analysis import TimeSeriesAnalyzer[m
[36m@@ -12,8 +12,9 @@[m [mfrom rag_implementation import RagImplementation[m
 from recommendation_generation import RecommendationGenerator[m
 from config import R2_CONFIG, LOGGING_CONFIG, GEMINI_CONFIG[m
 import pandas as pd[m
[31m-from r2_storage_manager import R2StorageManager  # <-- Now using R2StorageManager[m
[31m-from instagram_scraper import InstagramScraper  # <-- Add import[m
[32m+[m[32mfrom r2_storage_manager import R2StorageManager[m
[32m+[m[32mfrom instagram_scraper import InstagramScraper[m
[32m+[m[32mimport re[m
 [m
 # Set up logging[m
 logging.basicConfig([m
[36m@@ -29,7 +30,6 @@[m [mclass ContentRecommendationSystem:[m
         """Initialize all components of the system."""[m
         logger.info("Initializing Content Recommendation System")[m
         [m
[31m-        # Initialize components[m
         self.data_retriever = R2DataRetriever()[m
         self.vector_db = VectorDatabaseManager()[m
         self.time_series = TimeSeriesAnalyzer()[m
[36m@@ -38,152 +38,114 @@[m [mclass ContentRecommendationSystem:[m
             rag=self.rag,[m
             time_series=self.time_series[m
         )[m
[31m-        # Initialize R2 Storage Manager (for exporting to the tasks bucket)[m
         self.storage_manager = R2StorageManager()[m
     [m
     def ensure_sample_data_in_r2(self):[m
[31m-        """[m
[31m-        Ensure that sample data exists in the R2 bucket.[m
[31m-        This is a stub implementation. Add your logic here if needed.[m
[31m-        """[m
[31m-        logger.info("ensure_sample_data_in_r2: Stub implementation; no sample data was uploaded.")[m
[32m+[m[32m        """Ensure sample data exists in R2 (stub implementation)."""[m
[32m+[m[32m        logger.info("ensure_sample_data_in_r2: Stub implementation; no sample data uploaded.")[m
         return True[m
 [m
     def process_social_data(self, data_key):[m
[31m-        """[m
[31m-        Process social media data from R2.[m
[31m-        [m
[31m-        Args:[m
[31m-            data_key: Key of the data file in R2[m
[31m-            [m
[31m-        Returns:[m
[31m-            Dictionary with processed data or None if processing fails[m
[31m-        """[m
[32m+[m[32m        """Process social media data from R2."""[m
         try:[m
             logger.info(f"Processing social data from {data_key}")[m
             [m
[31m-            # Get data from R2[m
             raw_data = self.data_retriever.get_json_data(data_key)[m
[31m-            [m
[31m-            # Check if we have data[m
[31m-            if raw_data is None:  # Explicitly check for None[m
[32m+[m[32m            if raw_data is None:[m
                 logger.error(f"No data found at {data_key}")[m
                 return None[m
             [m
[31m-            # Case 1: Raw Instagram data coming as a list with a 'latestPosts' key in first element[m
             if isinstance(raw_data, list) and raw_data and 'latestPosts' in raw_data[0]:[m
                 data = self.process_instagram_data(raw_data)[m
                 if data:[m
                     logger.info("Successfully processed Instagram data")[m
[32m+[m[41m                    [m
[32m+[m[32m                    # Handle competitor data files[m
[32m+[m[32m                    if '/' in data_key:[m
[32m+[m[32m                        # Extract the parent directory from the key (e.g., "maccosmetics" from "maccosmetics/maccosmetics.json")[m
[32m+[m[32m                        parent_dir = data_key.split('/')[0][m
[32m+[m[32m                        # Load competitor files from the same directory[m
[32m+[m[32m                        competitors_data = self._load_competitor_files(parent_dir, data['profile']['username'])[m
[32m+[m[32m                        if competitors_data:[m
[32m+[m[32m                            data['competitor_posts'] = competitors_data[m
[32m+[m[32m                            logger.info(f"Added {len(competitors_data)} competitor posts to the data")[m
[32m+[m[41m                    [m
                     return data[m
[31m-                else:[m
[31m-                    logger.error("Failed to process Instagram data")[m
[31m-                    return None[m
[32m+[m[41m                    [m
[32m+[m[32m                logger.error("Failed to process Instagram data")[m
[32m+[m[32m                return None[m
             [m
[31m-            # Case 2: Already processed data (a dictionary with required keys)[m
             elif isinstance(raw_data, dict) and 'posts' in raw_data and 'engagement_history' in raw_data:[m
[31m-                logger.info("Data is already processed. Using it directly.")[m
[32m+[m[32m                logger.info("Data already processed. Using directly.")[m
                 return raw_data[m
             [m
[31m-            else:[m
[31m-                logger.error(f"Unsupported data format in {data_key}")[m
[31m-                return None[m
[32m+[m[32m            logger.error(f"Unsupported data format in {data_key}")[m
[32m+[m[32m            return None[m
                 [m
         except Exception as e:[m
[31m-            logger.error(f"Error processing social data: {str(e)}")[m
[32m+[m[32m            logger.error(f"Error processing social data from {data_key}: {str(e)}")[m
             import traceback[m
             logger.error(traceback.format_exc())[m
             return None[m
 [m
     def process_instagram_data(self, raw_data):[m
[31m-        """[m
[31m-        Process Instagram data format into the expected structure.[m
[31m-        [m
[31m-        Args:[m
[31m-            raw_data: Raw Instagram JSON data[m
[31m-            [m
[31m-        Returns:[m
[31m-            Dictionary with processed data in the expected format[m
[31m-        """[m
[32m+[m[32m        """Process Instagram data into expected structure."""[m
         try:[m
[31m-            # Check if data is in the expected Instagram format[m
             if not isinstance(raw_data, list) or not raw_data:[m
                 logger.warning("Invalid Instagram data format")[m
                 return None[m
             [m
[31m-            # Extract account data[m
             account_data = raw_data[0][m
[31m-            [m
[31m-            # Debug the structure[m
             logger.info(f"Instagram data keys: {list(account_data.keys())}")[m
             [m
[31m-            # Extract posts from latestPosts field[m
             posts = [][m
             engagement_history = [][m
             [m
[31m-            # Check if latestPosts exists in the account data[m
             if 'latestPosts' in account_data and isinstance(account_data['latestPosts'], list):[m
                 instagram_posts = account_data['latestPosts'][m
                 logger.info(f"Found {len(instagram_posts)} posts in latestPosts")[m
                 [m
                 for post in instagram_posts:[m
[31m-                    # Some posts might have childPosts (carousel posts)[m
                     if 'childPosts' in post and post['childPosts']:[m
                         logger.info(f"Post {post.get('id', '')} has {len(post['childPosts'])} child posts")[m
                     [m
[31m-                    # Create post object with required fields[m
                     post_obj = {[m
                         'id': post.get('id', ''),[m
                         'caption': post.get('caption', ''),[m
                         'hashtags': post.get('hashtags', []),[m
[31m-                        'engagement': 0,  # Will calculate below[m
[31m-                        'likes': 0,[m
[32m+[m[32m                        'engagement': 0,[m
[32m+[m[32m                        'likes': post.get('likesCount', 0) or 0,[m
                         'comments': post.get('commentsCount', 0),[m
                         'timestamp': post.get('timestamp', ''),[m
                         'url': post.get('url', ''),[m
[31m-                        'type': post.get('type', '')[m
[32m+[m[32m                        'type': post.get('type', ''),[m
[32m+[m[32m                        'username': account_data.get('username', '')[m
                     }[m
[31m-                    [m
[31m-                    # Handle likes which might be null[m
[31m-                    if post.get('likesCount') is not None:[m
[31m-                        post_obj['likes'] = post['likesCount'][m
[31m-                        [m
[31m-                    # Calculate engagement[m
                     post_obj['engagement'] = post_obj['likes'] + post_obj['comments'][m
                     [m
[31m-                    # Only add posts with captions[m
                     if post_obj['caption']:[m
                         posts.append(post_obj)[m
[31m-                        [m
[31m-                        # Add to engagement history if timestamp exists[m
                         if post.get('timestamp'):[m
[31m-                            engagement_record = {[m
[32m+[m[32m                            engagement_history.append({[m
                                 'timestamp': post.get('timestamp'),[m
                                 'engagement': post_obj['engagement'][m
[31m-                            }[m
[31m-                            engagement_history.append(engagement_record)[m
[32m+[m[32m                            })[m
             [m
[31m-            # Log post count for debugging[m
             logger.info(f"Processed {len(posts)} posts from Instagram data")[m
             [m
[31m-            # If no posts were processed, handle this case[m
             if not posts:[m
                 logger.warning("No posts extracted from Instagram data")[m
[31m-                # Create synthetic timestamps and engagement if needed for time series[m
                 now = datetime.now()[m
                 for i in range(3):[m
                     timestamp = (now - pd.Timedelta(days=i)).strftime('%Y-%m-%dT%H:%M:%S.000Z')[m
[31m-                    engagement = 1000 - (i * 100)  # Decreasing engagement[m
                     engagement_history.append({[m
                         'timestamp': timestamp,[m
[31m-                        'engagement': engagement[m
[32m+[m[32m                        'engagement': 1000 - (i * 100)[m
                     })[m
[31m-                logger.info(f"Created {len(engagement_history)} synthetic engagement records for time series")[m
[32m+[m[32m                logger.info(f"Created {len(engagement_history)} synthetic engagement records")[m
             [m
[31m-            # Sort engagement history by timestamp[m
             engagement_history.sort(key=lambda x: x['timestamp'])[m
             [m
[31m-            # Create processed data structure[m
             processed_data = {[m
                 'posts': posts,[m
                 'engagement_history': engagement_history,[m
[36m@@ -196,7 +158,6 @@[m [mclass ContentRecommendationSystem:[m
                     'account_type': account_data.get('account_type', 'unknown')[m
                 }[m
             }[m
[31m-            [m
             return processed_data[m
         [m
         except Exception as e:[m
[36m@@ -205,237 +166,396 @@[m [mclass ContentRecommendationSystem:[m
             logger.error(traceback.format_exc())[m
             return None[m
 [m
[31m-    def index_posts(self, posts):[m
[31m-        """[m
[31m-        Index posts in the vector database.[m
[31m-        [m
[31m-        Args:[m
[31m-            posts: List of post dictionaries[m
[31m-            [m
[31m-        Returns:[m
[31m-            Number of posts indexed[m
[31m-        """[m
[32m+[m[32m    def index_posts(self, posts, primary_username):[m
[32m+[m[32m        """Index posts in the vector database with primary_username."""[m
         try:[m
[31m-            logger.info(f"Indexing {len(posts)} posts")[m
[31m-            [m
[31m-            # Add posts to vector DB[m
[31m-            count = self.vector_db.add_posts(posts)[m
[31m-            [m
[32m+[m[32m            logger.info(f"Indexing {len(posts)} posts for {primary_username}")[m
[32m+[m[32m            count = self.vector_db.add_posts(posts, primary_username)[m
             logger.info(f"Successfully indexed {count} posts")[m
             return count[m
[31m-            [m
         except Exception as e:[m
             logger.error(f"Error indexing posts: {str(e)}")[m
             return 0[m
     [m
     def analyze_engagement(self, data):[m
[31m-        """[m
[31m-        Analyze engagement data.[m
[31m-        [m
[31m-        Args:[m
[31m-            data: Dictionary with engagement data[m
[31m-            [m
[31m-        Returns:[m
[31m-            Analysis results[m
[31m-        """[m
[32m+[m[32m        """Analyze engagement data."""[m
         try:[m
             logger.info("Analyzing engagement data")[m
[31m-            [m
[31m-            # Prepare engagement data[m
             if not data or not data.get('engagement_history'):[m
                 logger.warning("No engagement data found")[m
                 return None[m
             [m
[31m-            engagement_data = data['engagement_history'][m
[31m-            [m
[31m-            # Analyze with time series[m
[32m+[m[32m            engagement_data = pd.DataFrame(data['engagement_history'])[m
             results = self.time_series.analyze_data([m
                 engagement_data,[m
                 timestamp_col='timestamp',[m
                 value_col='engagement'[m
             )[m
[31m-            [m
             logger.info("Successfully analyzed engagement data")[m
             return results[m
[31m-            [m
         except Exception as e:[m
             logger.error(f"Error analyzing engagement: {str(e)}")[m
             return None[m
     [m
[31m-    def generate_content_plan(self, topics=None, n_recommendations=3):[m
[31m-        """[m
[31m-        Generate a content plan for given topics.[m
[31m-        [m
[31m-        Args:[m
[31m-            topics: List of topics (if None, detect trending)[m
[31m-            n_recommendations: Number of recommendations per topic[m
[31m-            [m
[31m-        Returns:[m
[31m-            Dictionary with content plan[m
[31m-        """[m
[32m+[m[32m    def generate_content_plan(self, data, topics=None, n_recommendations=3):[m
[32m+[m[32m        """Generate a content plan using updated RecommendationGenerator."""[m
         try:[m
             logger.info("Generating content plan")[m
             [m
[31m-            # If no topics provided, use trending topics[m
[31m-            if not topics:[m
[31m-                data = self.process_social_data()[m
[31m-                if data and data.get('engagement_history'):[m
[31m-                    trending = self.recommendation_generator.generate_trending_topics([m
[31m-                        data['engagement_history'],[m
[31m-                        top_n=3[m
[31m-                    )[m
[32m+[m[32m            if not data or not data.get('posts'):[m
[32m+[m[32m                logger.warning("No posts available for content plan generation")[m
[32m+[m[32m                return None[m
[32m+[m[41m            [m
[32m+[m[32m            profile = data.get('profile', {})[m
[32m+[m[32m            primary_username = profile.get('username', '')[m
[32m+[m[32m            if not primary_username:[m
[32m+[m[32m                logger.error("No primary username found in profile")[m
[32m+[m[32m                return None[m
[32m+[m[41m            [m
[32m+[m[32m            # Get competitor usernames from competitor_posts if available[m
[32m+[m[32m            if 'competitor_posts' in data and data['competitor_posts']:[m
[32m+[m[32m                # Extract unique usernames from competitor posts[m
[32m+[m[32m                secondary_usernames = list(set(post['username'] for post in data['competitor_posts'][m[41m [m
[32m+[m[32m                                               if 'username' in post and post['username'] != primary_username))[m
[32m+[m[32m                logger.info(f"Using {len(secondary_usernames)} competitor usernames from data: {secondary_usernames}")[m
[32m+[m[32m            else:[m
[32m+[m[32m                # Default fallback competitors[m
[32m+[m[32m                secondary_usernames = ["anastasiabeverlyhills", "fentybeauty"][m
[32m+[m[32m                logger.info(f"No competitor posts found, using default competitor usernames: {secondary_usernames}")[m
[32m+[m[41m            [m
[32m+[m[32m            query = "summer makeup trends"[m
[32m+[m[32m            if topics:[m
[32m+[m[32m                query = " ".join(topics) if isinstance(topics, list) else topics[m
[32m+[m[32m            elif data.get('engagement_history'):[m
[32m+[m[32m                trending = self.recommendation_generator.generate_trending_topics([m
[32m+[m[32m                    {e['timestamp']: e['engagement'] for e in data['engagement_history']},[m
[32m+[m[32m                    top_n=3[m
[32m+[m[32m                )[m
[32m+[m[32m                if trending:[m
                     topics = [trend['topic'] for trend in trending][m
[31m-                [m
[31m-                # Fallback topics if no trending detected[m
[31m-                if not topics:[m
[31m-                    topics = ["summer fashion", "product promotion", "customer engagement"][m
[31m-            [m
[31m-            # Generate recommendations[m
[31m-            recommendations = self.recommendation_generator.generate_recommendations([m
[31m-                topics,[m
[31m-                n_recommendations=n_recommendations[m
[32m+[m[32m                    query = " ".join(topics)[m
[32m+[m[41m            [m
[32m+[m[32m            # Combine primary and competitor posts for analysis[m
[32m+[m[32m            all_posts = data['posts'].copy()[m
[32m+[m[32m            if 'competitor_posts' in data and data['competitor_posts']:[m
[32m+[m[32m                all_posts.extend(data['competitor_posts'])[m
[32m+[m[32m                logger.info(f"Combined {len(data['posts'])} primary posts with {len(data['competitor_posts'])} competitor posts for analysis")[m
[32m+[m[41m            [m
[32m+[m[32m            content_plan = self.recommendation_generator.generate_content_plan([m
[32m+[m[32m                primary_username=primary_username,[m
[32m+[m[32m                secondary_usernames=secondary_usernames,[m
[32m+[m[32m                query=query,[m
[32m+[m[32m                posts=all_posts  # Use all posts for better context[m
             )[m
             [m
[31m-            # Create content plan[m
[31m-            content_plan = {[m
[31m-                'generated_date': datetime.now().strftime('%Y-%m-%d'),[m
[31m-                'topics': topics,[m
[31m-                'recommendations': recommendations[m
[31m-            }[m
[32m+[m[32m            if not content_plan:[m
[32m+[m[32m                logger.error("Failed to generate content plan")[m
[32m+[m[32m                return None[m
             [m
[31m-            logger.info(f"Successfully generated content plan with {len(topics)} topics")[m
[31m-            return content_plan[m
[32m+[m[32m            content_plan['profile_analysis'] = profile[m
[32m+[m[41m            [m
[32m+[m[32m            if 'trending_topics' in content_plan and content_plan['trending_topics']:[m
[32m+[m[32m                topics = [t['topic'] for t in content_plan['trending_topics']][m
[32m+[m[32m                batch_recs = self.recommendation_generator.generate_batch_recommendations([m
[32m+[m[32m                    topics,[m
[32m+[m[32m                    n_per_topic=n_recommendations[m
[32m+[m[32m                )[m
[32m+[m[32m                content_plan['batch_recommendations'] = batch_recs[m
             [m
[32m+[m[32m            logger.info(f"Successfully generated content plan for {primary_username}")[m
[32m+[m[32m            return content_plan[m
         except Exception as e:[m
             logger.error(f"Error generating content plan: {str(e)}")[m
             return None[m
     [m
     def save_content_plan(self, content_plan, filename='content_plan.json'):[m
[31m-        """[m
[31m-        Save content plan to a file.[m
[31m-        [m
[31m-        Args:[m
[31m-            content_plan: Dictionary with content plan[m
[31m-            filename: Output filename[m
[31m-            [m
[31m-        Returns:[m
[31m-            True if successful, False otherwise[m
[31m-        """[m
[32m+[m[32m        """Save content plan to a file."""[m
         try:[m
             logger.info(f"Saving content plan to {filename}")[m
[31m-            [m
             with open(filename, 'w') as f:[m
                 json.dump(content_plan, f, indent=2)[m
[31m-            [m
             logger.info(f"Successfully saved content plan to {filename}")[m
             return True[m
[31m-            [m
         except Exception as e:[m
             logger.error(f"Error saving content plan: {str(e)}")[m
             return False[m
 [m
     def export_content_plan_sections(self, content_plan):[m
[31m-        """Export content plan sections to R2 with username-based directory structure"""[m
[32m+[m[32m        """Export content plan sections to R2 with enhanced competitor analysis structure."""[m
         try:[m
[31m-            logger.info("Starting content plan export")[m
[32m+[m[32m            logger.info("Starting enhanced content plan export")[m
             [m
             if not content_plan:[m
                 logger.error("Cannot export empty content plan")[m
                 return False[m
 [m
[31m-            # Extract username from the processed data[m
[32m+[m[32m            # Get primary username[m
             username = content_plan.get('profile_analysis', {}).get('username')[m
             if not username:[m
                 logger.error("Cannot export - username not found in content plan")[m
                 return False[m
 [m
[31m-            # Validate required sections[m
[31m-            required_sections = {[m
[31m-                'recommendations': ['profile_analysis', 'improvement_recommendations', 'competitors'],[m
[31m-                'creative': ['next_post_prediction'][m
[31m-            }[m
[32m+[m[32m            # Create directory markers[m
[32m+[m[32m            self._ensure_directory_exists('recommendations')[m
[32m+[m[32m            self._ensure_directory_exists(f'recommendations/{username}')[m
             [m
[31m-            # Prepare recommendations export[m
[31m-            recommendations = {[m
[31m-                section: content_plan.get(section, {})[m
[31m-                for section in required_sections['recommendations'][m
[31m-            }[m
[32m+[m[32m            self._ensure_directory_exists('competitor_analysis')[m
[32m+[m[32m            self._ensure_directory_exists(f'competitor_analysis/{username}')[m
             [m
[31m-            # Prepare creative export[m
[31m-            creative = content_plan.get('next_post_prediction', {})[m
[31m-            if not creative.get('image_prompt') or not creative.get('caption'):[m
[31m-                logger.warning("Incomplete creative section in content plan")[m
[32m+[m[32m            self._ensure_directory_exists('next_posts')[m
[32m+[m[32m            self._ensure_directory_exists(f'next_posts/{username}')[m
 [m
[31m-            # Create file objects[m
[31m-            recommendations_file = io.BytesIO([m
[31m-                json.dumps(recommendations, indent=2).encode('utf-8')[m
[31m-            )[m
[31m-            creative_file = io.BytesIO([m
[31m-                json.dumps(creative, indent=2).encode('utf-8')[m
[31m-            )[m
[32m+[m[32m            # Set up the export paths based on the three main directories[m
[32m+[m[32m            results = {}[m
 [m
[31m-            # Export paths with username-based directory structure[m
[31m-            export_paths = {[m
[31m-                'recommendations': {[m
[31m-                    'key': f'recommendations/{username}/content_analysis.json',[m
[31m-                    'file': recommendations_file[m
[32m+[m[32m            # 1. Enhanced Recommendations section with competitor insights[m
[32m+[m[32m            recommendations_data = {[m
[32m+[m[32m                'recommendations': content_plan.get('recommendations', ''),[m
[32m+[m[32m                'primary_analysis': content_plan.get('primary_analysis', {}),[m
[32m+[m[32m                'additional_insights': content_plan.get('additional_insights', {}),[m
[32m+[m[32m                'competitive_advantage': {[m
[32m+[m[32m                    'strengths': self._extract_competitive_strengths(content_plan),[m
[32m+[m[32m                    'opportunities': self._extract_competitive_opportunities(content_plan)[m
                 },[m
[31m-                'creative': {[m
[31m-                    'key': f'next_post/{username}/next_post_prediction.json',[m