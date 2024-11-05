/* ###
 * IP: GHIDRA
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
// Attach an existing FID database.
// The functionality is similar to "Tools -> Function ID -> Attach existing FidDb..."
// but this script can be executed in both GUI and headless modes.
// The attached database can later be populated,
// for example by `CreateMultipleLibraries.java` when running in headless mode or
// by "Tools -> Function ID -> Populate FidDb from programs..." when running in GUI mode.
//@category FunctionID
import ghidra.app.script.GhidraScript;
import ghidra.feature.fid.db.FidFileManager;
import java.io.File;

public class AttachFidDatabase extends GhidraScript {

	@Override
	protected void run() throws Exception {
		File dbFile = askFile("Attach existing FidDb", "Attach");

		FidFileManager.getInstance().addUserFidFile(dbFile);
	}
}