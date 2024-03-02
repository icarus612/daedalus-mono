<script>
	import { DateCard } from '$components'
</script>

<div class="flex w-full min-h-max justify-center content-center px-10 py-20">
	<div class="basis-1/2 basis-1/3 px-20">
		<h1
			class="font-light text-9xl bg-gradient-to-br from-gray-600 via-gray-200 to-white inline-block text-transparent bg-clip-text"
		>
			Anna <br />
			&amp; <br />
			Ellis
		</h1>
    <h2 class="text-2xl font-bold">Together Forever</h2>
	</div>
	<div class="basis-2/3">
		<!-- Main content -->
		<div class="flex justify-center space-x-10">
			<!-- Image cards -->
			<DateCard
				imgSrc="first-date.jpg"
				imgText="01"
				header="12 MAR 2022"
				subHeader="THE FIRST DATE"
			/>
			<DateCard
				imgSrc="engagement.jpg"
				imgText="02"
				header="07 MAY 2023"
				subHeader="THE ENGAGEMENT"
			/>
			<DateCard
				imgSrc="forever-journey.jpg=w500"
				imgText="03"
				header="24 SEP 2023"
				subHeader="THE FOREVER JOURNEY"
			/>
		</div>
	</div>
</div>
