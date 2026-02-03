<template>
  <div class="showcase">
    <h1>API Showcase</h1>

    <!-- API Testing Section -->
    <section class="showcase-section">
      <h2>API Connection Status</h2>
      <div class="api-status">
        <Badge :variant="apiStatus === 'connected' ? 'success' : apiStatus === 'error' ? 'destructive' : 'warning'">
          {{ apiStatus === 'connected' ? '✓ Connected' : apiStatus === 'error' ? '✗ Disconnected' : '⏳ Checking...' }}
        </Badge>
        <span class="api-url">Base URL: {{ apiBaseUrl }}</span>
      </div>
    </section>

    <!-- Config APIs -->
    <section class="showcase-section">
      <h2>Config APIs</h2>
      <div class="api-card-row">
        <Card>
          <template #title>GET /config/models</template>
          <template #description>Fetch available ML models</template>
          <template #action>
            <Button size="sm" @click="testGetModels" :disabled="apiLoading.models">
              {{ apiLoading.models ? 'Loading...' : 'Test' }}
            </Button>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.models?.status" :variant="apiResponses.models.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.models.status }}
            </Badge>
            <pre v-if="apiResponses.models?.data">{{ JSON.stringify(apiResponses.models.data, null, 2) }}</pre>
            <span v-if="apiResponses.models?.error" class="error-text">{{ apiResponses.models.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>GET /config/query-strategies</template>
          <template #description>Fetch available query strategies</template>
          <template #action>
            <Button size="sm" @click="testGetStrategies" :disabled="apiLoading.strategies">
              {{ apiLoading.strategies ? 'Loading...' : 'Test' }}
            </Button>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.strategies?.status" :variant="apiResponses.strategies.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.strategies.status }}
            </Badge>
            <pre v-if="apiResponses.strategies?.data">{{ JSON.stringify(apiResponses.strategies.data, null, 2) }}</pre>
            <span v-if="apiResponses.strategies?.error" class="error-text">{{ apiResponses.strategies.error }}</span>
          </div>
        </Card>
      </div>
    </section>

    <!-- Active Learning APIs -->
    <section class="showcase-section">
      <h2>Active Learning APIs</h2>
      <div class="api-card-row">
        <Card>
          <template #title>GET /activelearning/instances</template>
          <template #description>List all active learning instances</template>
          <template #action>
            <Button size="sm" @click="testGetInstances" :disabled="apiLoading.instances">
              {{ apiLoading.instances ? 'Loading...' : 'Test' }}
            </Button>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.instances?.status" :variant="apiResponses.instances.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.instances.status }}
            </Badge>
            <pre v-if="apiResponses.instances?.data">{{ JSON.stringify(apiResponses.instances.data, null, 2) }}</pre>
            <span v-if="apiResponses.instances?.error" class="error-text">{{ apiResponses.instances.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>GET /activelearning/:id/info</template>
          <template #description>Get instance info (requires instance ID)</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="testInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testGetInstanceInfo" :disabled="apiLoading.instanceInfo || !testInstanceId">
                {{ apiLoading.instanceInfo ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.instanceInfo?.status" :variant="apiResponses.instanceInfo.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.instanceInfo.status }}
            </Badge>
            <pre v-if="apiResponses.instanceInfo?.data">{{ JSON.stringify(apiResponses.instanceInfo.data, null, 2) }}</pre>
            <span v-if="apiResponses.instanceInfo?.error" class="error-text">{{ apiResponses.instanceInfo.error }}</span>
          </div>
        </Card>
      </div>

      <div class="api-card-row" style="margin-top: 1rem">
        <Card>
          <template #title>GET /activelearning/:id/next</template>
          <template #description>Get next instances to label</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="testInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testGetNextInstances" :disabled="apiLoading.nextInstances || !testInstanceId">
                {{ apiLoading.nextInstances ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.nextInstances?.status" :variant="apiResponses.nextInstances.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.nextInstances.status }}
            </Badge>
            <pre v-if="apiResponses.nextInstances?.data">{{ JSON.stringify(apiResponses.nextInstances.data, null, 2) }}</pre>
            <span v-if="apiResponses.nextInstances?.error" class="error-text">{{ apiResponses.nextInstances.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>POST /activelearning/:id/save</template>
          <template #description>Save the trained model</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="testInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testSaveModel" :disabled="apiLoading.saveModel || !testInstanceId">
                {{ apiLoading.saveModel ? 'Saving...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.saveModel?.status" :variant="apiResponses.saveModel.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.saveModel.status }}
            </Badge>
            <pre v-if="apiResponses.saveModel?.data">{{ JSON.stringify(apiResponses.saveModel.data, null, 2) }}</pre>
            <span v-if="apiResponses.saveModel?.error" class="error-text">{{ apiResponses.saveModel.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>DELETE /activelearning/:id</template>
          <template #description>Delete an instance (⚠️ destructive)</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="deleteInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" variant="destructive" @click="testDeleteInstance" :disabled="apiLoading.deleteInstance || !deleteInstanceId">
                {{ apiLoading.deleteInstance ? 'Deleting...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.deleteInstance?.status" :variant="apiResponses.deleteInstance.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.deleteInstance.status }}
            </Badge>
            <pre v-if="apiResponses.deleteInstance?.data">{{ JSON.stringify(apiResponses.deleteInstance.data, null, 2) }}</pre>
            <span v-if="apiResponses.deleteInstance?.error" class="error-text">{{ apiResponses.deleteInstance.error }}</span>
          </div>
        </Card>
      </div>

      <div class="api-card-row" style="margin-top: 1rem">
        <Card padding="lg">
          <template #title>POST /activelearning/new</template>
          <template #description>Create a new active learning instance</template>
          <div class="resolution-form">
            <div class="form-row">
              <div class="form-field">
                <label>Model Name</label>
                <Select 
                  v-model="newInstanceData.model_name" 
                  :options="modelOptions" 
                  placeholder="Select a model..." 
                  :disabled="!modelOptions.length"
                />
                <span v-if="!modelOptions.length" class="hint-text">Load models first ↑</span>
              </div>
              <div class="form-field">
                <label>Query Strategy</label>
                <Select 
                  v-model="newInstanceData.qs_strategy" 
                  :options="strategyOptions" 
                  placeholder="Select a strategy..."
                  :disabled="!strategyOptions.length"
                />
                <span v-if="!strategyOptions.length" class="hint-text">Load strategies first ↑</span>
              </div>
            </div>
            <div class="info-box">
              <div class="info-row"><strong>Train Data:</strong> <code>data/al_demo_train_data.csv</code></div>
              <div class="info-row"><strong>Test Data:</strong> <code>data/al_demo_test_data.csv</code></div>
              <div class="info-row">
                <strong>Classes:</strong> 
                <Badge v-if="teamsForInstance.length" variant="success">{{ teamsForInstance.length }} teams loaded</Badge>
                <Button v-else size="sm" variant="outline" @click="loadTeamsForInstance" :disabled="apiLoading.teamsForInstance">
                  {{ apiLoading.teamsForInstance ? 'Loading...' : 'Load Teams' }}
                </Button>
              </div>
            </div>
            <Button 
              @click="testCreateInstance" 
              :disabled="apiLoading.createInstance || !newInstanceData.model_name || !newInstanceData.qs_strategy || !teamsForInstance.length"
            >
              {{ apiLoading.createInstance ? 'Creating...' : 'Create Instance' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.createInstance">
            <Badge :variant="apiResponses.createInstance.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.createInstance.status }}
            </Badge>
            <pre v-if="apiResponses.createInstance.data">{{ JSON.stringify(apiResponses.createInstance.data, null, 2) }}</pre>
            <span v-if="apiResponses.createInstance.error" class="error-text">{{ apiResponses.createInstance.error }}</span>
          </div>
        </Card>

        <Card padding="lg">
          <template #title>PUT /activelearning/:id/label</template>
          <template #description>Label instances</template>
          <div class="resolution-form">
            <div class="form-field">
              <label>Instance ID</label>
              <Input v-model="labelInstanceId" type="number" placeholder="Instance ID" />
            </div>
            <div class="form-field">
              <label>Query Indices (comma-separated)</label>
              <Input v-model="labelQueryIdxInput" placeholder="0, 1, 2" />
            </div>
            <div class="form-field">
              <label>Labels (comma-separated)</label>
              <Input v-model="labelLabelsInput" placeholder="label1, label2, label3" />
            </div>
            <Button @click="testLabelInstance" :disabled="apiLoading.labelInstance || !labelInstanceId">
              {{ apiLoading.labelInstance ? 'Labeling...' : 'Label Instances' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.labelInstance">
            <Badge :variant="apiResponses.labelInstance.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.labelInstance.status }}
            </Badge>
            <pre v-if="apiResponses.labelInstance.data">{{ JSON.stringify(apiResponses.labelInstance.data, null, 2) }}</pre>
            <span v-if="apiResponses.labelInstance.error" class="error-text">{{ apiResponses.labelInstance.error }}</span>
          </div>
        </Card>
      </div>
    </section>

    <!-- Data APIs -->
    <section class="showcase-section">
      <h2>Data APIs</h2>
      <div class="api-card-row">
        <Card>
          <template #title>GET /data/:id/teams</template>
          <template #description>Fetch available teams</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="dataInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testGetTeams" :disabled="apiLoading.teams">
                {{ apiLoading.teams ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.teams?.status" :variant="apiResponses.teams.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.teams.status }}
            </Badge>
            <pre v-if="apiResponses.teams?.data">{{ JSON.stringify(apiResponses.teams.data, null, 2) }}</pre>
            <span v-if="apiResponses.teams?.error" class="error-text">{{ apiResponses.teams.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>GET /data/:id/categories</template>
          <template #description>Fetch service categories</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="dataInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testGetCategories" :disabled="apiLoading.categories">
                {{ apiLoading.categories ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.categories?.status" :variant="apiResponses.categories.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.categories.status }}
            </Badge>
            <pre v-if="apiResponses.categories?.data">{{ JSON.stringify(apiResponses.categories.data, null, 2) }}</pre>
            <span v-if="apiResponses.categories?.error" class="error-text">{{ apiResponses.categories.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>GET /data/:id/subcategories</template>
          <template #description>Fetch service subcategories</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="dataInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testGetSubcategories" :disabled="apiLoading.subcategories">
                {{ apiLoading.subcategories ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.subcategories?.status" :variant="apiResponses.subcategories.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.subcategories.status }}
            </Badge>
            <pre v-if="apiResponses.subcategories?.data">{{ JSON.stringify(apiResponses.subcategories.data, null, 2) }}</pre>
            <span v-if="apiResponses.subcategories?.error" class="error-text">{{ apiResponses.subcategories.error }}</span>
          </div>
        </Card>
      </div>

      <div class="api-card-row" style="margin-top: 1rem">
        <Card padding="lg">
          <template #title>POST /data/:id/tickets</template>
          <template #description>Get tickets by indices</template>
          <div class="resolution-form">
            <div class="form-row">
              <div class="form-field">
                <label>Instance ID</label>
                <Input v-model="ticketsInstanceId" type="number" placeholder="Instance ID" />
              </div>
              <div class="form-field">
                <label>Train Data Path (optional)</label>
                <Input v-model="ticketsDataPath" placeholder="/path/to/data.csv" />
              </div>
            </div>
            <div class="form-field">
              <label>Ticket Indices (comma-separated)</label>
              <Input v-model="ticketIndicesInput" placeholder="0, 1, 2, 3" />
            </div>
            <Button @click="testGetTickets" :disabled="apiLoading.tickets">
              {{ apiLoading.tickets ? 'Loading...' : 'Get Tickets' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.tickets">
            <Badge :variant="apiResponses.tickets.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.tickets.status }}
            </Badge>
            <pre v-if="apiResponses.tickets.data">{{ JSON.stringify(apiResponses.tickets.data, null, 2) }}</pre>
            <span v-if="apiResponses.tickets.error" class="error-text">{{ apiResponses.tickets.error }}</span>
          </div>
        </Card>
      </div>
    </section>

    <!-- Resolution APIs -->
    <section class="showcase-section">
      <h2>Resolution APIs</h2>
      <div class="api-card-row">
        <Card padding="lg">
          <template #title>POST /resolution/process</template>
          <template #description>Process a ticket for resolution</template>
          <div class="resolution-form">
            <div class="form-field">
              <label>Ticket Title</label>
              <Input v-model="resolutionRequest.ticket_title" placeholder="Enter ticket title..." />
            </div>
            <div class="form-field">
              <label>Ticket Description</label>
              <Textarea v-model="resolutionRequest.ticket_description" placeholder="Enter ticket description..." />
            </div>
            <div class="form-row">
              <div class="form-field">
                <label>Service Category</label>
                <Input v-model="resolutionRequest.service_category" placeholder="Optional..." />
              </div>
              <div class="form-field">
                <label>Service Subcategory</label>
                <Input v-model="resolutionRequest.service_subcategory" placeholder="Optional..." />
              </div>
            </div>
            <Button @click="testProcessResolution" :disabled="apiLoading.resolution">
              {{ apiLoading.resolution ? 'Processing...' : 'Test Process Resolution' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.resolution">
            <Badge :variant="apiResponses.resolution.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.resolution.status }}
            </Badge>
            <pre v-if="apiResponses.resolution.data">{{ JSON.stringify(apiResponses.resolution.data, null, 2) }}</pre>
            <span v-if="apiResponses.resolution.error" class="error-text">{{ apiResponses.resolution.error }}</span>
          </div>
        </Card>
      </div>

      <div class="api-card-row" style="margin-top: 1rem">
        <Card padding="lg">
          <template #title>POST /resolution/feedback</template>
          <template #description>Submit feedback for a resolution</template>
          <div class="resolution-form">
            <div class="form-field">
              <label>Ticket Title</label>
              <Input v-model="feedbackRequest.ticket_title" placeholder="Enter ticket title..." />
            </div>
            <div class="form-field">
              <label>Ticket Description</label>
              <Textarea v-model="feedbackRequest.ticket_description" placeholder="Enter ticket description..." />
            </div>
            <div class="form-field">
              <label>Edited Response</label>
              <Textarea v-model="feedbackRequest.edited_response" placeholder="Enter edited response..." />
            </div>
            <Button @click="testSendFeedback" :disabled="apiLoading.feedback">
              {{ apiLoading.feedback ? 'Sending...' : 'Test Send Feedback' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.feedback">
            <Badge :variant="apiResponses.feedback.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.feedback.status }}
            </Badge>
            <pre v-if="apiResponses.feedback.data">{{ JSON.stringify(apiResponses.feedback.data, null, 2) }}</pre>
            <span v-if="apiResponses.feedback.error" class="error-text">{{ apiResponses.feedback.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>POST /resolution/rebuild-embeddings</template>
          <template #description>Force rebuild of embeddings cache (slow)</template>
          <template #action>
            <Button size="sm" variant="warning" @click="testRebuildEmbeddings" :disabled="apiLoading.rebuildEmbeddings">
              {{ apiLoading.rebuildEmbeddings ? 'Rebuilding...' : 'Rebuild' }}
            </Button>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.rebuildEmbeddings?.status" :variant="apiResponses.rebuildEmbeddings.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.rebuildEmbeddings.status }}
            </Badge>
            <pre v-if="apiResponses.rebuildEmbeddings?.data">{{ JSON.stringify(apiResponses.rebuildEmbeddings.data, null, 2) }}</pre>
            <span v-if="apiResponses.rebuildEmbeddings?.error" class="error-text">{{ apiResponses.rebuildEmbeddings.error }}</span>
          </div>
        </Card>
      </div>
    </section>

    <!-- Inference & XAI APIs -->
    <section class="showcase-section">
      <h2>Inference & XAI APIs</h2>
      <div class="api-card-row">
        <Card padding="lg">
          <template #title>POST /activelearning/:id/infer</template>
          <template #description>Run inference on ticket data</template>
          <div class="resolution-form">
            <div class="form-field">
              <label>Instance ID</label>
              <Input v-model="inferenceInstanceId" type="number" placeholder="Instance ID" />
            </div>
            <div class="form-field">
              <label>Title</label>
              <Input v-model="inferenceData.title_anon" placeholder="Ticket title..." />
            </div>
            <div class="form-field">
              <label>Description</label>
              <Textarea v-model="inferenceData.description_anon" placeholder="Ticket description..." />
            </div>
            <Button @click="testInference" :disabled="apiLoading.inference || !inferenceInstanceId">
              {{ apiLoading.inference ? 'Running...' : 'Test Inference' }}
            </Button>
          </div>
          <div class="api-response" v-if="apiResponses.inference">
            <Badge :variant="apiResponses.inference.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.inference.status }}
            </Badge>
            <pre v-if="apiResponses.inference.data">{{ JSON.stringify(apiResponses.inference.data, null, 2) }}</pre>
            <span v-if="apiResponses.inference.error" class="error-text">{{ apiResponses.inference.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>POST /xai/:id/explain_lime</template>
          <template #description>Get LIME explanation for prediction</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="xaiInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testExplainLime" :disabled="apiLoading.lime || !xaiInstanceId">
                {{ apiLoading.lime ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.lime?.status" :variant="apiResponses.lime.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.lime.status }}
            </Badge>
            <pre v-if="apiResponses.lime?.data">{{ JSON.stringify(apiResponses.lime.data, null, 2) }}</pre>
            <span v-if="apiResponses.lime?.error" class="error-text">{{ apiResponses.lime.error }}</span>
          </div>
        </Card>

        <Card>
          <template #title>POST /xai/:id/nearest_ticket</template>
          <template #description>Find nearest similar ticket</template>
          <template #action>
            <div class="api-action-row">
              <Input v-model="xaiInstanceId" type="number" placeholder="ID" style="width: 80px" />
              <Button size="sm" @click="testNearestTicket" :disabled="apiLoading.nearestTicket || !xaiInstanceId">
                {{ apiLoading.nearestTicket ? 'Loading...' : 'Test' }}
              </Button>
            </div>
          </template>
          <div class="api-response">
            <Badge v-if="apiResponses.nearestTicket?.status" :variant="apiResponses.nearestTicket.status === 'success' ? 'success' : 'destructive'">
              {{ apiResponses.nearestTicket.status }}
            </Badge>
            <pre v-if="apiResponses.nearestTicket?.data">{{ JSON.stringify(apiResponses.nearestTicket.data, null, 2) }}</pre>
            <span v-if="apiResponses.nearestTicket?.error" class="error-text">{{ apiResponses.nearestTicket.error }}</span>
          </div>
        </Card>
      </div>
    </section>

    <!-- Test All APIs Button -->
    <section class="showcase-section">
      <h2>Batch Testing</h2>
      <Card>
        <template #title>Test All Read-Only APIs</template>
        <template #description>Run all GET endpoints to verify API connectivity</template>
        <div class="batch-actions">
          <Button @click="testAllApis" :disabled="batchTesting">
            {{ batchTesting ? 'Testing...' : 'Run All Tests' }}
          </Button>
          <Button variant="outline" @click="clearAllResponses">Clear Results</Button>
        </div>
        <div class="batch-results" v-if="batchResults.length > 0">
          <div v-for="result in batchResults" :key="result.endpoint" class="batch-result-item">
            <Badge :variant="result.success ? 'success' : 'destructive'">
              {{ result.success ? '✓' : '✗' }}
            </Badge>
            <span class="endpoint-name">{{ result.endpoint }}</span>
            <span class="response-time">{{ result.time }}ms</span>
          </div>
        </div>
      </Card>
    </section>

    <hr class="section-divider" />

    <h1>Component Showcase</h1>

    <!-- Input Showcase -->
    <section class="showcase-section">
      <h2>Input - Basic Types</h2>
      <div class="input-row">
        <div class="input-demo">
          <label>Text Input</label>
          <Input v-model="inputText" placeholder="Enter some text..." />
        </div>
        <div class="input-demo">
          <label>Email Input</label>
          <Input v-model="inputEmail" type="email" placeholder="email@example.com" />
        </div>
        <div class="input-demo">
          <label>Password Input</label>
          <Input v-model="inputPassword" type="password" placeholder="Enter password..." />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Input - Other Types</h2>
      <div class="input-row">
        <div class="input-demo">
          <label>Number Input</label>
          <Input v-model="inputNumber" type="number" placeholder="0" :min="0" :max="100" />
        </div>
        <div class="input-demo">
          <label>Search Input</label>
          <Input v-model="inputSearch" type="search" placeholder="Search..." />
        </div>
        <div class="input-demo">
          <label>Date Input</label>
          <Input type="date" />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Input - States</h2>
      <div class="input-row">
        <div class="input-demo">
          <label>Disabled</label>
          <Input v-model="inputDisabled" disabled />
        </div>
        <div class="input-demo">
          <label>Read-only</label>
          <Input model-value="Read-only content" readonly />
        </div>
        <div class="input-demo">
          <label>Invalid</label>
          <Input model-value="Invalid input" :aria-invalid="true" />
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Textarea Showcase</h1>

    <section class="showcase-section">
      <h2>Textarea - Basic</h2>
      <div class="textarea-row">
        <div class="textarea-demo">
          <label>Basic Textarea</label>
          <Textarea v-model="textareaBasic" placeholder="Enter your message..." />
        </div>
        <div class="textarea-demo">
          <label>With Content</label>
          <Textarea v-model="textareaWithValue" />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Textarea - States</h2>
      <div class="textarea-row">
        <div class="textarea-demo">
          <label>Disabled</label>
          <Textarea v-model="textareaDisabled" disabled />
        </div>
        <div class="textarea-demo">
          <label>Invalid</label>
          <Textarea model-value="This input has an error" :aria-invalid="true" />
        </div>
        <div class="textarea-demo">
          <label>With Character Limit</label>
          <Textarea v-model="textareaBasic" placeholder="Max 100 characters..." :maxlength="100" />
          <span class="char-count">{{ textareaBasic.length }}/100</span>
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Checkbox Showcase</h1>

    <section class="showcase-section">
      <h2>Checkbox - Basic States</h2>
      <div class="checkbox-row">
        <div class="checkbox-demo">
          <Checkbox v-model="checkboxBasic" id="checkbox-basic" />
          <label for="checkbox-basic">Unchecked</label>
        </div>
        <div class="checkbox-demo">
          <Checkbox v-model="checkboxChecked" id="checkbox-checked" />
          <label for="checkbox-checked">Checked</label>
        </div>
        <div class="checkbox-demo">
          <Checkbox v-model="checkboxIndeterminate" id="checkbox-indeterminate" />
          <label for="checkbox-indeterminate">Indeterminate</label>
        </div>
        <div class="checkbox-demo">
          <Checkbox v-model="checkboxDisabled" id="checkbox-disabled" disabled />
          <label for="checkbox-disabled">Disabled</label>
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Checkbox - Form Usage</h2>
      <Card>
        <template #title>
          <span class="title-with-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
            </svg>
            Notification Preferences
          </span>
        </template>
        <template #description>Choose what you want to receive</template>
        <div class="checkbox-list">
          <div class="checkbox-list-item">
            <Checkbox v-model="checkboxTerms" id="terms" />
            <div class="checkbox-label-group">
              <label for="terms">Accept terms and conditions</label>
              <span class="checkbox-description">You agree to our Terms of Service and Privacy Policy.</span>
            </div>
          </div>
          <div class="checkbox-list-item">
            <Checkbox v-model="checkboxNewsletter" id="newsletter" />
            <div class="checkbox-label-group">
              <label for="newsletter">Subscribe to newsletter</label>
              <span class="checkbox-description">Receive updates about new features and releases.</span>
            </div>
          </div>
          <div class="checkbox-list-item">
            <Checkbox v-model="checkboxNotifications" id="notifications" />
            <div class="checkbox-label-group">
              <label for="notifications">Enable push notifications</label>
              <span class="checkbox-description">Get notified about important events in real-time.</span>
            </div>
          </div>
        </div>
        <template #footer>
          <div class="card-footer-actions">
            <Button variant="outline">Cancel</Button>
            <Button>Save Preferences</Button>
          </div>
        </template>
      </Card>
    </section>

    <hr class="section-divider" />

    <h1>Accordion Showcase</h1>

    <section class="showcase-section">
      <h2>Accordion - Single (Collapsible)</h2>
      <Card padding="sm">
        <Accordion v-model="accordionSingle" type="single" collapsible>
          <AccordionItem value="item-1">
            <AccordionTrigger>Is it accessible?</AccordionTrigger>
            <AccordionContent>
              Yes. It adheres to the WAI-ARIA design pattern and supports keyboard navigation.
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-2">
            <AccordionTrigger>Is it styled?</AccordionTrigger>
            <AccordionContent>
              Yes. It comes with default styles that match your design system. You can also customize it using CSS variables.
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-3">
            <AccordionTrigger>Is it animated?</AccordionTrigger>
            <AccordionContent>
              Yes. The accordion content smoothly transitions when opening and closing, providing a pleasant user experience.
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </section>

    <section class="showcase-section">
      <h2>Accordion - Multiple</h2>
      <Card padding="sm">
        <Accordion v-model="accordionMultiple" type="multiple">
          <AccordionItem value="item-1">
            <AccordionTrigger>Can I open multiple items?</AccordionTrigger>
            <AccordionContent>
              Yes! When using type="multiple", you can have multiple accordion items open at the same time.
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-2">
            <AccordionTrigger>How do I control it?</AccordionTrigger>
            <AccordionContent>
              You can use v-model to control which items are open. For multiple type, it accepts an array of values.
            </AccordionContent>
          </AccordionItem>
          <AccordionItem value="item-3" disabled>
            <AccordionTrigger>Can items be disabled?</AccordionTrigger>
            <AccordionContent>
              Yes, individual items can be disabled by passing the disabled prop.
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </Card>
    </section>

    <section class="showcase-section">
      <h2>Accordion - FAQ Example</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>
              </svg>
              Frequently Asked Questions
            </span>
          </template>
          <Accordion type="single" collapsible>
            <AccordionItem value="faq-1">
              <AccordionTrigger>What payment methods do you accept?</AccordionTrigger>
              <AccordionContent>
                We accept all major credit cards (Visa, MasterCard, American Express), PayPal, and bank transfers for annual subscriptions.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="faq-2">
              <AccordionTrigger>Can I cancel my subscription?</AccordionTrigger>
              <AccordionContent>
                Yes, you can cancel your subscription at any time. Your access will continue until the end of your current billing period.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="faq-3">
              <AccordionTrigger>Is there a free trial?</AccordionTrigger>
              <AccordionContent>
                Yes! We offer a 14-day free trial with full access to all features. No credit card required to start.
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>
      </div>
    </section>

    <hr class="section-divider" />

    <!-- Card Showcase -->
    <section class="showcase-section">
      <h2>Card - Variants</h2>
      <div class="card-row">
        <Card variant="default">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/>
              </svg>
              Default Card
            </span>
          </template>
          <template #description>This is the default variant with a border</template>
          <p>Card content goes here. This demonstrates the default styling.</p>
        </Card>

        <Card variant="outline">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
              </svg>
              Outline Card
            </span>
          </template>
          <template #description>Transparent background with border</template>
          <p>This variant has no background fill.</p>
        </Card>

        <Card variant="elevated">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2"/><path d="m9 12 2 2 4-4"/>
              </svg>
              Elevated Card
            </span>
          </template>
          <template #description>Uses box-shadow instead of border</template>
          <p>This variant appears lifted with a subtle shadow.</p>
        </Card>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Card - With Actions</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              Project Settings
            </span>
          </template>
          <template #description>Manage your project configuration</template>
          <template #action>
            <Button variant="ghost" size="icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/>
              </svg>
            </Button>
          </template>
          <p>Configure your project settings and preferences here.</p>
        </Card>

        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
              </svg>
              Notifications
            </span>
          </template>
          <template #description>You have 3 unread messages</template>
          <template #action>
            <Button variant="secondary" size="sm">View All</Button>
          </template>
          <p>Stay updated with the latest activity in your workspace.</p>
        </Card>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Card - With Footer</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M5 12h14"/><path d="M12 5v14"/>
              </svg>
              Create New Item
            </span>
          </template>
          <template #description>Fill in the details below</template>
          <p>This card demonstrates the footer slot with action buttons aligned at the bottom.</p>
          <template #footer>
            <div class="card-footer-actions">
              <Button variant="outline">Cancel</Button>
              <Button>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>
                </svg>
                Save
              </Button>
            </div>
          </template>
        </Card>

        <Card variant="elevated">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" x2="10" y1="11" y2="17"/><line x1="14" x2="14" y1="11" y2="17"/>
              </svg>
              Confirm Deletion
            </span>
          </template>
          <template #description>Are you sure you want to proceed?</template>
          <p>This action cannot be undone. Please review before confirming.</p>
          <template #footer>
            <div class="card-footer-actions">
              <Button variant="ghost">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>
                </svg>
                Go Back
              </Button>
              <Button variant="destructive">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>
                </svg>
                Delete
              </Button>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Card - Padding Variants</h2>
      <div class="card-row">
        <Card padding="sm">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>
              </svg>
              Small Padding
            </span>
          </template>
          <p>Compact card with minimal spacing.</p>
        </Card>

        <Card padding="default">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" x2="21" y1="9" y2="9"/><line x1="9" x2="9" y1="21" y2="9"/>
              </svg>
              Default Padding
            </span>
          </template>
          <p>Standard spacing for most use cases.</p>
        </Card>

        <Card padding="lg">
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="18" height="18" x="3" y="3" rx="2"/><path d="M21 12H3"/><path d="M12 3v18"/>
              </svg>
              Large Padding
            </span>
          </template>
          <p>More spacious layout for emphasis.</p>
        </Card>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Card - Content Only (Stats)</h2>
      <div class="card-row">
        <Card>
          <div class="stat-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            <span class="stat-value">1,234</span>
            <span class="stat-label">Total Users</span>
          </div>
        </Card>

        <Card variant="elevated">
          <div class="stat-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon stat-icon--success">
              <path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/>
            </svg>
            <span class="stat-value">98.5%</span>
            <span class="stat-label">Uptime</span>
          </div>
        </Card>

        <Card variant="outline">
          <div class="stat-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon stat-icon--warning">
              <path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
            </svg>
            <span class="stat-value">67%</span>
            <span class="stat-label">Storage Used</span>
          </div>
        </Card>

        <Card>
          <div class="stat-content">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="stat-icon stat-icon--info">
              <path d="M3 3v16a2 2 0 0 0 2 2h16"/><path d="m19 9-5 5-4-4-3 3"/>
            </svg>
            <span class="stat-value">+24%</span>
            <span class="stat-label">Growth Rate</span>
          </div>
        </Card>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Progress Showcase</h1>

    <section class="showcase-section">
      <h2>Basic Progress</h2>
      <div class="progress-row">
        <div class="progress-item">
          <span class="progress-label">0%</span>
          <Progress :value="0" />
        </div>
        <div class="progress-item">
          <span class="progress-label">25%</span>
          <Progress :value="25" />
        </div>
        <div class="progress-item">
          <span class="progress-label">50%</span>
          <Progress :value="50" />
        </div>
        <div class="progress-item">
          <span class="progress-label">75%</span>
          <Progress :value="75" />
        </div>
        <div class="progress-item">
          <span class="progress-label">100%</span>
          <Progress :value="100" />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Progress with Custom Max</h2>
      <div class="progress-row">
        <div class="progress-item">
          <span class="progress-label">3 of 10 steps</span>
          <Progress :value="3" :max="10" />
        </div>
        <div class="progress-item">
          <span class="progress-label">7 of 10 steps</span>
          <Progress :value="7" :max="10" />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Color Variants</h2>
      <div class="progress-row">
        <div class="progress-item">
          <span class="progress-label">Default</span>
          <Progress :value="60" color="default" />
        </div>
        <div class="progress-item">
          <span class="progress-label">Success</span>
          <Progress :value="100" color="success" />
        </div>
        <div class="progress-item">
          <span class="progress-label">Warning</span>
          <Progress :value="75" color="warning" />
        </div>
        <div class="progress-item">
          <span class="progress-label">Danger</span>
          <Progress :value="90" color="danger" />
        </div>
        <div class="progress-item">
          <span class="progress-label">Info</span>
          <Progress :value="45" color="info" />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Progress in Cards</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
              </svg>
              File Upload
            </span>
          </template>
          <template #description>Uploading documents...</template>
          <div class="card-progress">
            <Progress :value="67" />
            <span class="progress-percent">67%</span>
          </div>
        </Card>

        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/>
              </svg>
              Course Progress
            </span>
          </template>
          <template #description>Introduction to Machine Learning</template>
          <div class="card-progress">
            <Progress :value="8" :max="12" />
            <span class="progress-percent">8 / 12 modules</span>
          </div>
        </Card>

        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/>
              </svg>
              Storage Used
            </span>
          </template>
          <template #description>4.2 GB of 10 GB used</template>
          <div class="card-progress">
            <Progress :value="42" />
            <span class="progress-percent">42%</span>
          </div>
        </Card>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Select Showcase</h1>

    <section class="showcase-section">
      <h2>Basic Select</h2>
      <div class="select-row">
        <div class="select-demo">
          <label>Choose a fruit</label>
          <Select v-model="selectedFruit" :options="fruitOptions" placeholder="Select a fruit..." />
          <span class="select-value-display">Selected: {{ selectedFruit || 'None' }}</span>
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>With Groups</h2>
      <div class="select-row">
        <div class="select-demo">
          <label>Choose a framework</label>
          <Select v-model="selectedFramework" :options="frameworkOptions" placeholder="Select a framework..." />
          <span class="select-value-display">Selected: {{ selectedFramework || 'None' }}</span>
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Size Variants</h2>
      <div class="select-row">
        <div class="select-demo">
          <label>Small size</label>
          <Select v-model="selectedSize" :options="sizeOptions" placeholder="Small select..." size="sm" />
        </div>
        <div class="select-demo">
          <label>Default size</label>
          <Select v-model="selectedSize" :options="sizeOptions" placeholder="Default select..." />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>With Disabled Items</h2>
      <div class="select-row">
        <div class="select-demo">
          <label>Timezone</label>
          <Select v-model="selectedTimezone" :options="timezoneOptions" placeholder="Select timezone..." />
        </div>
        <div class="select-demo">
          <label>Disabled Select</label>
          <Select :options="sizeOptions" placeholder="Disabled..." disabled />
        </div>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Select in Card</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
              </svg>
              User Preferences
            </span>
          </template>
          <template #description>Configure your account settings</template>
          <div class="card-form">
            <div class="form-field">
              <label>Language</label>
              <Select v-model="selectedLanguage" :options="languageOptions" placeholder="Select language..." />
            </div>
            <div class="form-field">
              <label>Theme</label>
              <Select v-model="selectedTheme" :options="themeOptions" placeholder="Select theme..." />
            </div>
          </div>
          <template #footer>
            <div class="card-footer-actions">
              <Button variant="outline">Cancel</Button>
              <Button>Save Preferences</Button>
            </div>
          </template>
        </Card>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Button Showcase</h1>

    <section class="showcase-section">
      <h2>Variants</h2>
      <div class="button-row">
        <Button variant="default">Default</Button>
        <Button variant="secondary">Secondary</Button>
        <Button variant="destructive">Destructive</Button>
        <Button variant="outline">Outline</Button>
        <Button variant="ghost">Ghost</Button>
        <Button variant="link">Link</Button>
        <Button variant="success">Success</Button>
        <Button variant="warning">Warning</Button>
        <Button variant="info">Info</Button>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Sizes</h2>
      <div class="button-row">
        <Button size="sm">Small</Button>
        <Button size="default">Default</Button>
        <Button size="lg">Large</Button>
        <Button size="icon">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M5 12h14"/><path d="M12 5v14"/>
          </svg>
        </Button>
      </div>
    </section>

    <section class="showcase-section">
      <h2>With Icons</h2>
      <div class="button-row">
        <Button>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/>
          </svg>
          Upload
        </Button>
        <Button variant="outline">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/>
          </svg>
          Download
        </Button>
        <Button variant="secondary">
          Settings
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="m9 18 6-6-6-6"/>
          </svg>
        </Button>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Disabled State</h2>
      <div class="button-row">
        <Button disabled>Default</Button>
        <Button variant="secondary" disabled>Secondary</Button>
        <Button variant="destructive" disabled>Destructive</Button>
        <Button variant="outline" disabled>Outline</Button>
      </div>
    </section>

    <section class="showcase-section">
      <h2>All Variants × All Sizes</h2>
      <div class="button-grid">
        <div v-for="variant in variants" :key="variant" class="button-row">
          <span class="variant-label">{{ variant }}</span>
          <Button v-for="size in sizes" :key="size" :variant="variant" :size="size">
            {{ size === 'icon' ? '' : size }}
            <svg v-if="size === 'icon'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
            </svg>
          </Button>
        </div>
      </div>
    </section>

    <hr class="section-divider" />

    <h1>Badge Showcase</h1>

    <section class="showcase-section">
      <h2>Badge - Variants</h2>
      <div class="badge-row">
        <Badge variant="default">Default</Badge>
        <Badge variant="secondary">Secondary</Badge>
        <Badge variant="destructive">Destructive</Badge>
        <Badge variant="outline">Outline</Badge>
        <Badge variant="success">Success</Badge>
        <Badge variant="warning">Warning</Badge>
        <Badge variant="info">Info</Badge>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Badge - With Icons</h2>
      <div class="badge-row">
        <Badge variant="success">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/>
          </svg>
          Verified
        </Badge>
        <Badge variant="warning">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
          </svg>
          Pending
        </Badge>
        <Badge variant="destructive">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/>
          </svg>
          Error
        </Badge>
        <Badge variant="info">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>
          </svg>
          Info
        </Badge>
        <Badge variant="outline">
          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2v20M2 12h20"/>
          </svg>
          New
        </Badge>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Badge - As Links</h2>
      <div class="badge-row">
        <Badge as="a" href="#" variant="default">Link Badge</Badge>
        <Badge as="a" href="#" variant="secondary">Secondary Link</Badge>
        <Badge as="a" href="#" variant="outline">Outline Link</Badge>
      </div>
    </section>

    <section class="showcase-section">
      <h2>Badge - Use Cases</h2>
      <div class="card-row">
        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
              User Status
            </span>
          </template>
          <div class="badge-use-case">
            <div class="badge-use-case-item">
              <span>John Doe</span>
              <Badge variant="default">
                <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                  <circle cx="12" cy="12" r="6"/>
                </svg>
                Online
              </Badge>
            </div>
            <div class="badge-use-case-item">
              <span>Jane Smith</span>
              <Badge variant="secondary">Away</Badge>
            </div>
            <div class="badge-use-case-item">
              <span>Bob Wilson</span>
              <Badge variant="outline">Offline</Badge>
            </div>
          </div>
        </Card>

        <Card>
          <template #title>
            <span class="title-with-icon">
              <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.375 2.625a1 1 0 0 1 3 3l-9.013 9.014a2 2 0 0 1-.853.505l-2.873.84a.5.5 0 0 1-.62-.62l.84-2.873a2 2 0 0 1 .506-.852z"/>
              </svg>
              Task Labels
            </span>
          </template>
          <div class="badge-use-case">
            <div class="badge-use-case-item">
              <span>Fix login bug</span>
              <div class="badge-group">
                <Badge variant="destructive">Bug</Badge>
                <Badge variant="outline">High Priority</Badge>
              </div>
            </div>
            <div class="badge-use-case-item">
              <span>Add dark mode</span>
              <div class="badge-group">
                <Badge variant="secondary">Feature</Badge>
                <Badge variant="outline">Low Priority</Badge>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { ref, reactive, onMounted, computed } from 'vue'
import Button from '@/components/ui/Button.vue'
import Badge from '@/components/ui/Badge.vue'
import Card from '@/components/ui/Card.vue'
import Progress from '@/components/ui/Progress.vue'
import Select from '@/components/ui/Select.vue'
import Input from '@/components/ui/Input.vue'
import Textarea from '@/components/ui/Textarea.vue'
import Checkbox from '@/components/ui/Checkbox.vue'
import { Accordion, AccordionItem, AccordionTrigger, AccordionContent } from '@/components/ui/Accordion.vue'
import type { SelectOptions } from '@/components/ui/Select.vue'
import { apiService } from '@/services/api'
import type { ResolutionProcessRequest, ResolutionFeedbackRequest, InferenceData, NewInstanceRequest } from '@/types/api'

// API Base URL
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// API Status
const apiStatus = ref<'checking' | 'connected' | 'error'>('checking')

// API Test Instance IDs
const testInstanceId = ref('')
const dataInstanceId = ref('0')
const inferenceInstanceId = ref('')
const xaiInstanceId = ref('')
const deleteInstanceId = ref('')
const labelInstanceId = ref('')
const ticketsInstanceId = ref('0')

// New Instance Form - hardcoded paths for demo
const TRAIN_DATA_PATH = 'data/al_demo_train_data.csv'
const TEST_DATA_PATH = 'data/al_demo_test_data.csv'

const newInstanceData = reactive<NewInstanceRequest>({
  model_name: '',
  qs_strategy: '',
  class_list: [],
  train_data_path: TRAIN_DATA_PATH,
  test_data_path: TEST_DATA_PATH,
})
const teamsForInstance = ref<string[]>([])

// Label Instance Form
const labelQueryIdxInput = ref('')
const labelLabelsInput = ref('')

// Tickets Form
const ticketIndicesInput = ref('0, 1, 2')
const ticketsDataPath = ref('')

// API Loading States
const apiLoading = reactive({
  models: false,
  strategies: false,
  instances: false,
  instanceInfo: false,
  nextInstances: false,
  teams: false,
  categories: false,
  subcategories: false,
  resolution: false,
  feedback: false,
  inference: false,
  lime: false,
  teamsForInstance: false,
  createInstance: false,
  labelInstance: false,
  saveModel: false,
  deleteInstance: false,
  tickets: false,
  nearestTicket: false,
  rebuildEmbeddings: false,
})

// API Responses
interface ApiResponse {
  status: 'success' | 'error'
  data?: unknown
  error?: string
}

const apiResponses = reactive<Record<string, ApiResponse | null>>({
  models: null,
  strategies: null,
  instances: null,
  instanceInfo: null,
  nextInstances: null,
  teams: null,
  categories: null,
  subcategories: null,
  resolution: null,
  feedback: null,
  inference: null,
  lime: null,
  createInstance: null,
  labelInstance: null,
  saveModel: null,
  deleteInstance: null,
  tickets: null,
  nearestTicket: null,
  rebuildEmbeddings: null,
})

// Computed options for selects (from API responses)
const modelOptions = computed<SelectOptions>(() => {
  const data = apiResponses.models?.data as { models?: string[] } | undefined
  if (!data?.models) return []
  return data.models.map(model => ({ value: model, label: model }))
})

const strategyOptions = computed<SelectOptions>(() => {
  const data = apiResponses.strategies?.data as { strategies?: string[] } | undefined
  if (!data?.strategies) return []
  return data.strategies.map(strategy => ({ value: strategy, label: strategy }))
})

// Resolution Request Data
const resolutionRequest = reactive<ResolutionProcessRequest>({
  ticket_title: 'Cannot access email',
  ticket_description: 'I am unable to login to my email account. It shows an error message.',
  service_category: '',
  service_subcategory: '',
})

// Feedback Request Data
const feedbackRequest = reactive<ResolutionFeedbackRequest>({
  ticket_title: 'Cannot access email',
  ticket_description: 'I am unable to login to my email account.',
  edited_response: 'Please try resetting your password using the self-service portal.',
})

// Inference Data
const inferenceData = reactive<InferenceData>({
  title_anon: 'Network connectivity issue',
  description_anon: 'Unable to connect to the corporate network from home.',
})

// Batch Testing
const batchTesting = ref(false)
const batchResults = ref<Array<{ endpoint: string; success: boolean; time: number }>>([])

// API Test Functions
async function testGetModels() {
  apiLoading.models = true
  try {
    const data = await apiService.getModels()
    apiResponses.models = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.models = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.models = false
  }
}

async function testGetStrategies() {
  apiLoading.strategies = true
  try {
    const data = await apiService.getQueryStrategies()
    apiResponses.strategies = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.strategies = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.strategies = false
  }
}

async function testGetInstances() {
  apiLoading.instances = true
  try {
    const data = await apiService.getInstances()
    apiResponses.instances = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.instances = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.instances = false
  }
}

async function testGetInstanceInfo() {
  if (!testInstanceId.value) return
  apiLoading.instanceInfo = true
  try {
    const data = await apiService.getInstanceInfo(Number(testInstanceId.value))
    apiResponses.instanceInfo = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.instanceInfo = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.instanceInfo = false
  }
}

async function testGetNextInstances() {
  if (!testInstanceId.value) return
  apiLoading.nextInstances = true
  try {
    const data = await apiService.getNextInstances(Number(testInstanceId.value))
    apiResponses.nextInstances = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.nextInstances = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.nextInstances = false
  }
}

async function testGetTeams() {
  apiLoading.teams = true
  try {
    const data = await apiService.getTeams(Number(dataInstanceId.value) || 0)
    apiResponses.teams = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.teams = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.teams = false
  }
}

async function testGetCategories() {
  apiLoading.categories = true
  try {
    const data = await apiService.getCategories(Number(dataInstanceId.value) || 0)
    apiResponses.categories = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.categories = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.categories = false
  }
}

async function testGetSubcategories() {
  apiLoading.subcategories = true
  try {
    const data = await apiService.getSubcategories(Number(dataInstanceId.value) || 0)
    apiResponses.subcategories = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.subcategories = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.subcategories = false
  }
}

async function testProcessResolution() {
  apiLoading.resolution = true
  try {
    const data = await apiService.processResolution(resolutionRequest)
    apiResponses.resolution = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.resolution = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.resolution = false
  }
}

async function testSendFeedback() {
  apiLoading.feedback = true
  try {
    const data = await apiService.sendResolutionFeedback(feedbackRequest)
    apiResponses.feedback = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.feedback = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.feedback = false
  }
}

async function testInference() {
  if (!inferenceInstanceId.value) return
  apiLoading.inference = true
  try {
    const data = await apiService.infer(Number(inferenceInstanceId.value), inferenceData)
    apiResponses.inference = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.inference = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.inference = false
  }
}

async function testExplainLime() {
  if (!xaiInstanceId.value) return
  apiLoading.lime = true
  try {
    const data = await apiService.explainLime(Number(xaiInstanceId.value), { ticket_data: inferenceData })
    apiResponses.lime = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.lime = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.lime = false
  }
}

async function testNearestTicket() {
  if (!xaiInstanceId.value) return
  apiLoading.nearestTicket = true
  try {
    const data = await apiService.findNearestTicket(Number(xaiInstanceId.value), { ticket_data: inferenceData })
    apiResponses.nearestTicket = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.nearestTicket = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.nearestTicket = false
  }
}

async function loadTeamsForInstance() {
  apiLoading.teamsForInstance = true
  try {
    const data = await apiService.getTeams(0, TRAIN_DATA_PATH)
    teamsForInstance.value = data.teams || []
  } catch (err: unknown) {
    console.error('Failed to load teams:', err)
    teamsForInstance.value = []
  } finally {
    apiLoading.teamsForInstance = false
  }
}

async function testCreateInstance() {
  apiLoading.createInstance = true
  try {
    const data = await apiService.createInstance({
      ...newInstanceData,
      class_list: teamsForInstance.value,
    })
    apiResponses.createInstance = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.createInstance = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.createInstance = false
  }
}

async function testLabelInstance() {
  if (!labelInstanceId.value) return
  apiLoading.labelInstance = true
  try {
    const queryIdx = labelQueryIdxInput.value.split(',').map(s => s.trim()).filter(Boolean)
    const labels = labelLabelsInput.value.split(',').map(s => s.trim()).filter(Boolean)
    const data = await apiService.labelInstance(Number(labelInstanceId.value), {
      query_idx: queryIdx,
      labels: labels,
    })
    apiResponses.labelInstance = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.labelInstance = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.labelInstance = false
  }
}

async function testSaveModel() {
  if (!testInstanceId.value) return
  apiLoading.saveModel = true
  try {
    const data = await apiService.saveModel(Number(testInstanceId.value))
    apiResponses.saveModel = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.saveModel = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.saveModel = false
  }
}

async function testDeleteInstance() {
  if (!deleteInstanceId.value) return
  apiLoading.deleteInstance = true
  try {
    const data = await apiService.deleteInstance(Number(deleteInstanceId.value))
    apiResponses.deleteInstance = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.deleteInstance = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.deleteInstance = false
  }
}

async function testGetTickets() {
  apiLoading.tickets = true
  try {
    const indices = ticketIndicesInput.value.split(',').map(s => s.trim()).filter(Boolean)
    const data = await apiService.getTickets(
      Number(ticketsInstanceId.value) || 0,
      indices,
      ticketsDataPath.value || undefined
    )
    apiResponses.tickets = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.tickets = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.tickets = false
  }
}

async function testRebuildEmbeddings() {
  apiLoading.rebuildEmbeddings = true
  try {
    const data = await apiService.rebuildEmbeddings()
    apiResponses.rebuildEmbeddings = { status: 'success', data }
  } catch (err: unknown) {
    apiResponses.rebuildEmbeddings = { status: 'error', error: err instanceof Error ? err.message : 'Unknown error' }
  } finally {
    apiLoading.rebuildEmbeddings = false
  }
}

async function testAllApis() {
  batchTesting.value = true
  batchResults.value = []
  
  const tests = [
    { name: 'GET /config/models', fn: apiService.getModels },
    { name: 'GET /config/query-strategies', fn: apiService.getQueryStrategies },
    { name: 'GET /activelearning/instances', fn: apiService.getInstances },
    { name: 'GET /data/0/teams', fn: () => apiService.getTeams(0) },
    { name: 'GET /data/0/categories', fn: () => apiService.getCategories(0) },
    { name: 'GET /data/0/subcategories', fn: () => apiService.getSubcategories(0) },
  ]

  for (const test of tests) {
    const start = performance.now()
    try {
      await test.fn()
      batchResults.value.push({
        endpoint: test.name,
        success: true,
        time: Math.round(performance.now() - start),
      })
    } catch {
      batchResults.value.push({
        endpoint: test.name,
        success: false,
        time: Math.round(performance.now() - start),
      })
    }
  }
  
  batchTesting.value = false
}

function clearAllResponses() {
  Object.keys(apiResponses).forEach(key => {
    apiResponses[key] = null
  })
  batchResults.value = []
}

// Check API connectivity on mount
onMounted(async () => {
  try {
    await apiService.getModels()
    apiStatus.value = 'connected'
  } catch {
    apiStatus.value = 'error'
  }
})

const badgeVariants = ['default', 'secondary', 'destructive', 'outline', 'success', 'warning', 'info'] as const

const variants = ['default', 'secondary', 'destructive', 'outline', 'ghost', 'link', 'success', 'warning', 'info'] as const
const sizes = ['sm', 'default', 'lg', 'icon'] as const

// Input demo values
const inputText = ref('')
const inputEmail = ref('')
const inputPassword = ref('')
const inputNumber = ref('')
const inputSearch = ref('')
const inputDisabled = ref('Disabled input')

// Textarea demo values
const textareaBasic = ref('')
const textareaWithValue = ref('This is some example text that shows how the textarea handles pre-filled content.')
const textareaDisabled = ref('This textarea is disabled')

// Checkbox demo values
const checkboxBasic = ref(false)
const checkboxChecked = ref(true)
const checkboxIndeterminate = ref<boolean | 'indeterminate'>('indeterminate')
const checkboxDisabled = ref(false)
const checkboxTerms = ref(false)
const checkboxNewsletter = ref(true)
const checkboxNotifications = ref(false)

// Accordion demo values
const accordionSingle = ref('item-1')
const accordionMultiple = ref<string[]>(['item-1'])

// Select demo values
const selectedFruit = ref('')
const selectedFramework = ref('')
const selectedSize = ref('')
const selectedTimezone = ref('')
const selectedLanguage = ref('en')
const selectedTheme = ref('system')

// Options
const fruitOptions: SelectOptions = [
  { value: 'apple', label: '🍎 Apple' },
  { value: 'banana', label: '🍌 Banana' },
  { value: 'orange', label: '🍊 Orange' },
  { value: 'grape', label: '🍇 Grape' },
  { value: 'strawberry', label: '🍓 Strawberry' }
]

const frameworkOptions: SelectOptions = [
  {
    label: 'Frontend',
    options: [
      { value: 'vue', label: 'Vue.js' },
      { value: 'react', label: 'React' },
      { value: 'angular', label: 'Angular' },
      { value: 'svelte', label: 'Svelte' }
    ]
  },
  {
    label: 'Backend',
    options: [
      { value: 'express', label: 'Express.js' },
      { value: 'fastapi', label: 'FastAPI' },
      { value: 'django', label: 'Django' },
      { value: 'rails', label: 'Ruby on Rails' }
    ]
  }
]

const sizeOptions: SelectOptions = [
  { value: 'option1', label: 'Option 1' },
  { value: 'option2', label: 'Option 2' },
  { value: 'option3', label: 'Option 3' }
]

const timezoneOptions: SelectOptions = [
  { value: 'utc', label: 'UTC' },
  { value: 'est', label: 'Eastern Time (EST)' },
  { value: 'pst', label: 'Pacific Time (PST)' },
  { value: 'gmt', label: 'GMT (Unavailable)', disabled: true },
  { value: 'cet', label: 'Central European (CET)' }
]

const languageOptions: SelectOptions = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Español' },
  { value: 'fr', label: 'Français' },
  { value: 'de', label: 'Deutsch' }
]

const themeOptions: SelectOptions = [
  { value: 'light', label: 'Light' },
  { value: 'dark', label: 'Dark' },
  { value: 'system', label: 'System' }
]
</script>

<style lang="scss" scoped>
.showcase {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
  overflow-x: hidden;
}

.showcase-section {
  margin-bottom: 2.5rem;

  h2 {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border);
  }
}

/* API Showcase Styles */
.api-status {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.api-url {
  font-size: 0.875rem;
  color: var(--muted-foreground);
  font-family: monospace;
}

.api-card-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.api-response {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
  
  pre {
    margin-top: 0.5rem;
    padding: 0.75rem;
    background: var(--muted);
    border-radius: 0.375rem;
    font-size: 0.75rem;
    overflow-x: auto;
    max-height: 200px;
    overflow-y: auto;
  }
}

.error-text {
  color: hsl(0, 84%, 60%);
  font-size: 0.875rem;
}

.hint-text {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  font-style: italic;
}

.info-box {
  padding: 0.75rem;
  background: var(--muted);
  border-radius: 0.375rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  
  code {
    font-size: 0.75rem;
    padding: 0.125rem 0.375rem;
    background: var(--background);
    border-radius: 0.25rem;
    border: 1px solid var(--border);
  }
}

.api-action-row {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.resolution-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.batch-actions {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.batch-results {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border);
}

.batch-result-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: var(--muted);
  border-radius: 0.375rem;
}

.endpoint-name {
  flex: 1;
  font-family: monospace;
  font-size: 0.875rem;
}

.response-time {
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

/* End API Showcase Styles */

.button-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.button-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.variant-label {
  width: 100px;
  font-size: 0.875rem;
  color: var(--muted-foreground);
  text-transform: capitalize;
}

.card-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.card-footer-actions {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}

.stat-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 1rem 0;
}

.stat-icon {
  color: var(--muted-foreground);
  margin-bottom: 0.75rem;

  &--success {
    color: #22c55e;
  }

  &--warning {
    color: #f59e0b;
  }

  &--info {
    color: #3b82f6;
  }
}

.stat-value {
  font-size: 2rem;
  font-weight: var(--font-weight-medium);
  line-height: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--muted-foreground);
  margin-top: 0.5rem;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    flex-shrink: 0;
  }
}

.section-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 3rem 0;
}

.progress-row {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progress-label {
  font-size: 0.875rem;
  color: var(--muted-foreground);
}

.card-progress {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-top: 0.5rem;
}

.progress-percent {
  font-size: 0.875rem;
  color: var(--muted-foreground);
  white-space: nowrap;
}

.select-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
}

.select-demo {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 250px;
  flex: 1;
  max-width: 300px;

  label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
  }
}

.select-value-display {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  margin-top: 0.25rem;
}

.card-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
  }
}

.input-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
}

.input-demo {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  min-width: 200px;
  flex: 1;
  max-width: 300px;

  label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
  }
}

.textarea-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
}

.textarea-demo {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  flex: 1;
  min-width: 280px;

  label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
  }
}

.char-count {
  font-size: 0.75rem;
  color: var(--muted-foreground);
  text-align: right;
}

.checkbox-row {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem;
}

.checkbox-demo {
  display: flex;
  align-items: center;
  gap: 0.5rem;

  label {
    font-size: 0.875rem;
    cursor: pointer;
  }
}

.checkbox-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.checkbox-list-item {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.checkbox-label-group {
  display: flex;
  flex-direction: column;
  gap: 0.125rem;

  label {
    font-size: 0.875rem;
    font-weight: var(--font-weight-medium);
    cursor: pointer;
  }
}

.checkbox-description {
  font-size: 0.75rem;
  color: var(--muted-foreground);
}

.badge-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.badge-group {
  display: flex;
  gap: 0.5rem;
}

.badge-use-case {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.badge-use-case-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);

  &:last-child {
    border-bottom: none;
  }

  span {
    font-size: 0.875rem;
  }
}
</style>